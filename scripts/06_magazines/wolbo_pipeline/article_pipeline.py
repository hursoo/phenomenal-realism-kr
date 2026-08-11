"""Article-level orchestrator. v1.0 (2026-05-09)

정책 v0.3 §3 통합 파이프라인. OCR(S1)은 별도 실행, 본 스크립트는 S2~S5 오케스트레이션.

Stages (S=auto, H=human):
  S1. ocr           외부: run_gemini_ocr.py / run_paddle_ocr.py / Claude (수기) — 본 스크립트 외
  S2. consensus     consensus.py review + draft → review_*.md + <id>.high_fidelity.draft_v0.md
  H3. high_fidelity Soo가 draft_v0의 ⚠️ 마커 해소 → <id>.high_fidelity.md (인간만)
  S4. transform     transform_old_to_modern.py로 (3) raw 생성
  S5. spacing       add_spacing.py로 띄어쓰기 부여 (Claude API)
  H6. final         Soo 검수 → 본 article 권위 텍스트 확정 (인간만)

Usage:
    python article_pipeline.py status --article 01_kwonyu_1911-01
    python article_pipeline.py next   --article 01_kwonyu_1911-01    # 다음 auto 단계 실행
    python article_pipeline.py run    --article 01_kwonyu_1911-01 --stage consensus
"""
from __future__ import annotations
import argparse
import subprocess
import sys
from pathlib import Path

import yaml

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

BASE = Path(r'C:/hp_data/0_tnt/hyeonsang/_ocr_experiments/cheondogyo_wolbo_series')
SCRIPTS = BASE / 'scripts'

REQUIRED_ENGINES = ['claude_opus_4_7', 'gemini', 'paddle']

STAGES = ['ocr', 'consensus', 'high_fidelity', 'transform', 'spacing', 'final']
AUTO_STAGES = {'consensus', 'transform', 'spacing'}
HUMAN_STAGES = {'ocr', 'high_fidelity', 'final'}


def resolve_article_dir(arg: str) -> Path:
    p = Path(arg)
    if p.is_absolute() and p.exists():
        return p
    candidate = BASE / arg
    if candidate.exists():
        return candidate
    for sub in ('articles', 'samples'):
        candidate = BASE / sub / arg
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f'Cannot resolve article path: {arg}')


def load_meta(article_dir: Path) -> dict:
    return yaml.safe_load((article_dir / 'meta.yaml').read_text(encoding='utf-8'))


def discover_units(meta: dict) -> list[dict]:
    return meta.get('units') or meta.get('units_extracted') or []


# ============================================================
# 단계별 상태 탐지
# ============================================================

def state_ocr(article_dir: Path, units: list[dict]) -> tuple[bool, str]:
    """모든 unit × {claude, gemini, paddle}에 OCR 결과가 있는가?"""
    missing = []
    for u in units:
        for eng in REQUIRED_ENGINES:
            txt = article_dir / 'ocr' / eng / f'{u["id"]}.txt'
            if not txt.exists():
                missing.append(f'{eng}/{u["id"]}.txt')
    if missing:
        return False, f'missing {len(missing)} OCR files (e.g. {missing[0]})'
    return True, f'all {len(units) * len(REQUIRED_ENGINES)} OCR files present'


def state_consensus(article_dir: Path) -> tuple[bool, str]:
    """draft_v0 + 모든 unit의 review_*.md가 있는가?"""
    transcripts = article_dir / 'transcripts'
    drafts = list(transcripts.glob('*.high_fidelity.draft_v0.md')) if transcripts.exists() else []
    reviews = list((article_dir / 'ocr').glob('review_*.md'))
    if not drafts:
        return False, 'no draft_v0 file (run consensus draft)'
    if not reviews:
        return False, 'no review_*.md files (run consensus review)'
    return True, f'{len(drafts)} draft + {len(reviews)} review files'


def state_high_fidelity(article_dir: Path) -> tuple[bool, str]:
    """draft_v0가 아닌 high_fidelity.md가 있는가? (Soo가 마커 해소 완료 신호)"""
    transcripts = article_dir / 'transcripts'
    if not transcripts.exists():
        return False, 'transcripts/ missing'
    finals = [p for p in transcripts.glob('*.high_fidelity.md') if 'draft_v0' not in p.name]
    if not finals:
        return False, '(2) high_fidelity (non-draft) 미작성 — Soo 마커 해소 대기'
    return True, f'{len(finals)} high_fidelity file(s): {[p.name for p in finals]}'


def state_transform(article_dir: Path) -> tuple[bool, str]:
    """(3) modern_reading.md가 있는가?"""
    transcripts = article_dir / 'transcripts'
    if not transcripts.exists():
        return False, 'transcripts/ missing'
    mr = list(transcripts.glob('*.modern_reading.md'))
    if not mr:
        return False, '(3) modern_reading.md 없음 — transform 단계 필요'
    return True, f'{len(mr)} modern_reading file(s): {[p.name for p in mr]}'


def state_spacing(article_dir: Path) -> tuple[bool, str]:
    """modern_reading.md의 status frontmatter가 auto_with_spacing인가?"""
    transcripts = article_dir / 'transcripts'
    if not transcripts.exists():
        return False, 'transcripts/ missing'
    mr_files = list(transcripts.glob('*.modern_reading.md'))
    if not mr_files:
        return False, '(3) 없음 — transform 선행 필요'
    spaced = []
    for p in mr_files:
        text = p.read_text(encoding='utf-8')
        if 'status: auto_with_spacing' in text or 'status: human_verified' in text:
            spaced.append(p.name)
    if not spaced:
        return False, '(3)에 띄어쓰기 미부여 — add_spacing 필요'
    return True, f'spaced: {spaced}'


def state_final(article_dir: Path) -> tuple[bool, str]:
    """Soo 최종 검수 끝. status: human_verified 또는 status: final."""
    transcripts = article_dir / 'transcripts'
    if not transcripts.exists():
        return False, 'transcripts/ missing'
    final_files = []
    for p in transcripts.glob('*.modern_reading.md'):
        text = p.read_text(encoding='utf-8')
        if 'status: human_verified' in text or 'status: final' in text:
            final_files.append(p.name)
    if not final_files:
        return False, 'Soo 최종 검수 대기 (status: human_verified or final로 갱신 시 완료)'
    return True, f'final: {final_files}'


STATE_FUNCS = {
    'ocr': state_ocr,
    'consensus': state_consensus,
    'high_fidelity': state_high_fidelity,
    'transform': state_transform,
    'spacing': state_spacing,
    'final': state_final,
}


def assess_state(article_dir: Path, units: list[dict]) -> list[tuple[str, bool, str]]:
    """각 단계의 (이름, 완료 여부, 메시지)."""
    rows = []
    for stage in STAGES:
        fn = STATE_FUNCS[stage]
        if stage == 'ocr':
            done, msg = fn(article_dir, units)
        else:
            done, msg = fn(article_dir)
        rows.append((stage, done, msg))
    return rows


# ============================================================
# 단계 실행
# ============================================================

def run_consensus(article_dir: Path, slug: str) -> int:
    print(f'\n→ Stage S2 consensus: review + draft\n')
    cmds = [
        [sys.executable, str(SCRIPTS / 'consensus.py'), 'review', '--article', slug],
        [sys.executable, str(SCRIPTS / 'consensus.py'), 'draft', '--article', slug],
    ]
    for cmd in cmds:
        print(f'$ {" ".join(cmd)}')
        result = subprocess.run(cmd, cwd=BASE)
        if result.returncode != 0:
            return result.returncode
    return 0


def run_transform(article_dir: Path) -> int:
    print(f'\n→ Stage S4 transform: (2) → (3) 자동 변환\n')
    transcripts = article_dir / 'transcripts'
    finals = [p for p in transcripts.glob('*.high_fidelity.md') if 'draft_v0' not in p.name]
    if not finals:
        print('ERROR: high_fidelity (non-draft) 파일 없음 — H3 단계 미완료', file=sys.stderr)
        return 1
    src = finals[0]
    dst = src.with_name(src.name.replace('.high_fidelity.md', '.modern_reading.md'))
    cmd = [sys.executable, str(SCRIPTS / 'transform_old_to_modern.py'), str(src), str(dst)]
    print(f'$ {" ".join(cmd)}')
    return subprocess.run(cmd, cwd=BASE).returncode


def run_spacing(article_dir: Path) -> int:
    print(f'\n→ Stage S5 spacing: Claude API 띄어쓰기 부여\n')
    transcripts = article_dir / 'transcripts'
    mr_files = list(transcripts.glob('*.modern_reading.md'))
    if not mr_files:
        print('ERROR: modern_reading.md 없음 — S4 transform 미완료', file=sys.stderr)
        return 1
    src = mr_files[0]
    cmd = [sys.executable, str(SCRIPTS / 'add_spacing.py'), str(src)]
    print(f'$ {" ".join(cmd)}')
    return subprocess.run(cmd, cwd=BASE).returncode


RUN_FUNCS = {
    'consensus': run_consensus,
    'transform': run_transform,
    'spacing': run_spacing,
}


HUMAN_GUIDANCE = {
    'ocr': '''S1. OCR (인간/엔진별 스크립트):
    - run_gemini_ocr.py, run_paddle_ocr.py 호출 (현재 article 단위로 일반화 필요 — 75편 일괄 시 정비)
    - claude_opus_4_7는 수기 OCR (vision 입력)
    - 출력: <article>/ocr/{claude_opus_4_7,gemini,paddle}/<unit_id>.txt''',
    'high_fidelity': '''H3. Soo 마커 해소 (인간):
    - 입력: <article>/transcripts/<id>.high_fidelity.draft_v0.md (⚠️ 마커 N개)
    - 모든 ⚠️[C:..|G:..|P:..] 마커를 시각 대조 후 정확한 텍스트로 교체
    - 정책 v0.3 §1-16에 따라 해소
    - 완료 시: 파일을 <id>.high_fidelity.md로 이름 변경 (.draft_v0 제거), status: draft_v1''',
    'final': '''H6. Soo 최종 검수 (인간):
    - (3) modern_reading.md의 띄어쓰기·구두점 자연성 검토
    - 정책 v0.3 §20.b 7규칙 준수 여부 확인
    - 완료 시: frontmatter status를 `human_verified` 또는 `final`로 갱신''',
}


# ============================================================
# CLI
# ============================================================

def cmd_status(article_dir: Path, units: list[dict]) -> int:
    print(f'\n=== Pipeline status: {article_dir.name} ===\n')
    rows = assess_state(article_dir, units)
    width = max(len(r[0]) for r in rows)
    for stage, done, msg in rows:
        kind = 'S' if stage in AUTO_STAGES else 'H'
        mark = '✓' if done else '·'
        print(f'  {mark} [{kind}] {stage:<{width}s}  {msg}')

    next_stage = next((s for s, done, _ in rows if not done), None)
    print()
    if next_stage is None:
        print('All stages complete.')
    else:
        kind = 'auto' if next_stage in AUTO_STAGES else 'HUMAN'
        print(f'Next stage: {next_stage} ({kind})')
        if next_stage in HUMAN_STAGES:
            print()
            print(HUMAN_GUIDANCE.get(next_stage, ''))
    return 0


def cmd_next(article_dir: Path, slug: str, units: list[dict]) -> int:
    rows = assess_state(article_dir, units)
    next_stage = next((s for s, done, _ in rows if not done), None)
    if next_stage is None:
        print('All stages complete.')
        return 0
    if next_stage in HUMAN_STAGES:
        print(f'Next stage `{next_stage}` is HUMAN — 자동 실행 불가.\n')
        print(HUMAN_GUIDANCE.get(next_stage, ''))
        return 0
    return RUN_FUNCS[next_stage](article_dir, slug) if next_stage == 'consensus' else RUN_FUNCS[next_stage](article_dir)


def cmd_run(article_dir: Path, slug: str, stage: str) -> int:
    if stage in HUMAN_STAGES:
        print(f'Stage `{stage}` is HUMAN — 자동 실행 불가.\n')
        print(HUMAN_GUIDANCE.get(stage, ''))
        return 0
    fn = RUN_FUNCS.get(stage)
    if fn is None:
        print(f'ERROR: unknown stage `{stage}`', file=sys.stderr)
        return 1
    return fn(article_dir, slug) if stage == 'consensus' else fn(article_dir)


def main() -> int:
    ap = argparse.ArgumentParser(description='Article pipeline orchestrator v1.0')
    ap.add_argument('command', choices=['status', 'next', 'run'])
    ap.add_argument('--article', '-a', required=True, help='article slug or path')
    ap.add_argument('--stage', '-s', help='stage name (for `run` command)')
    args = ap.parse_args()

    article_dir = resolve_article_dir(args.article)
    meta = load_meta(article_dir)
    units = discover_units(meta)
    if not units:
        print(f'ERROR: no units in {article_dir / "meta.yaml"}', file=sys.stderr)
        return 1

    if args.command == 'status':
        return cmd_status(article_dir, units)
    elif args.command == 'next':
        return cmd_next(article_dir, args.article, units)
    elif args.command == 'run':
        if not args.stage:
            print('ERROR: --stage required for `run`', file=sys.stderr)
            return 1
        return cmd_run(article_dir, args.article, args.stage)
    return 1


if __name__ == '__main__':
    sys.exit(main())
