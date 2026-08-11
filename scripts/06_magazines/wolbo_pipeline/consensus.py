"""3-engine consensus pipeline for cheondogyo_wolbo series. v1.0 (2026-05-09)

Article-agnostic 합의 분석. articles/<id>/ 또는 samples/<id>/의 meta.yaml을 읽어
units를 자동 발견. ocr/<engine>/<unit_id>.txt를 입력으로, 단별 review·draft 산출.

권위 정책: _design/2026-05-09_cheondogyo_wolbo_consensus_policy_v0_3.md (20규칙).

도구 조합 (정책 §7-9):
  - claude_opus_4_7  주 도구 (큰 활자·표제·옛한글 우세)
  - gemini           보강 도구 (작은 활자·본문 cross-check)
  - paddle           검증 도구 (한자 시각 유사자)
  - gpt5             정확도 부족으로 제외 (있어도 무시)

Modes:
  analyze   — 단일 unit 상세 통계 (--unit 지정)
  all       — 한 article의 모든 unit 요약 표
  review    — 단별 review_<unit>.md 산출 (인간 중재 보조 docs)
  draft     — (2) 고충실본 draft v0 자동 초안 생성 (인라인 ⚠️ 마커)

Usage:
  python consensus.py review  --article 01_kwonyu_1911-01
  python consensus.py all     --article 01_kwonyu_1911-01
  python consensus.py analyze --article 01_kwonyu_1911-01 --unit unit_3_p2u
  python consensus.py draft   --article 01_kwonyu_1911-01

  --article는 slug, BASE 상대경로, 또는 절대경로 모두 허용.
"""
from __future__ import annotations
import argparse
import difflib
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

# Windows 콘솔 cp949 → utf-8 (옛한글·한자 출력용)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

BASE = Path(r'C:/hp_data/0_tnt/hyeonsang/_ocr_experiments/cheondogyo_wolbo_series')

# 정책 v0.3 §7-9: 시리즈 채택 도구. gpt5는 제외.
DEFAULT_ENGINES = ['claude_opus_4_7', 'gemini', 'paddle']
EXCLUDED_ENGINES = {'gpt5'}


# ============================================================
# Article·unit 발견
# ============================================================

def resolve_article_dir(arg: str) -> Path:
    """Accept absolute path, BASE-relative path, or just slug."""
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
    """meta.yaml의 units 또는 units_extracted 키를 처리."""
    return meta.get('units') or meta.get('units_extracted') or []


def discover_engines(article_dir: Path) -> list[str]:
    """article_dir/ocr/ 하위의 엔진 디렉토리 자동 발견. EXCLUDED는 제외."""
    ocr_dir = article_dir / 'ocr'
    if not ocr_dir.exists():
        return []
    found = [p.name for p in ocr_dir.iterdir()
             if p.is_dir() and p.name not in EXCLUDED_ENGINES and not p.name.startswith('_')]
    # DEFAULT_ENGINES 순서를 유지하며 발견된 것만 반환
    ordered = [e for e in DEFAULT_ENGINES if e in found]
    extras = [e for e in found if e not in DEFAULT_ENGINES]
    return ordered + extras


def unit_paths(article_dir: Path, unit_id: str, engines: list[str]) -> dict[str, Path]:
    return {eng: article_dir / 'ocr' / eng / f'{unit_id}.txt' for eng in engines}


# ============================================================
# 텍스트 정제·분류
# ============================================================

def load_clean(path: Path) -> str:
    """Strip headers, [tag] labels, blank lines; return continuous chars."""
    if not path.exists():
        return ''
    raw = path.read_text(encoding='utf-8')
    out = []
    for line in raw.splitlines():
        if line.startswith('#') or line.startswith('---'):
            continue
        cleaned = re.sub(r'\[[^\]]+\]\s*', '', line)
        cleaned = cleaned.strip()
        if cleaned:
            out.append(cleaned)
    return ''.join(out)


def is_hanja(c: str) -> bool:
    return 0x3400 <= ord(c) <= 0x9FFF


def is_modern_hangul(c: str) -> bool:
    return 0xAC00 <= ord(c) <= 0xD7A3


def is_jamo(c: str) -> bool:
    o = ord(c)
    return (0x1100 <= o <= 0x11FF) or (0xA960 <= o <= 0xA97F) or (0xD7B0 <= o <= 0xD7FF) or o == 0x3163 or 0x3131 <= o <= 0x318F


def hanja_only(text: str) -> str:
    return ''.join(c for c in text if is_hanja(c))


def stats(text: str) -> dict:
    return {
        'total': len(text),
        'hanja': sum(1 for c in text if is_hanja(c)),
        'hangul': sum(1 for c in text if is_modern_hangul(c)),
        'jamo': sum(1 for c in text if is_jamo(c)),
        'arae_h': text.count('ᄒᆞ'),  # ㅎ + 아래아 결합
    }


def get_text(texts: dict, name: str) -> str:
    return texts.get(name, '')


# ============================================================
# Diff·합의 핵심 로직
# ============================================================

def pairwise_diffs(a: str, b: str) -> list[tuple]:
    """Return non-equal opcodes from SequenceMatcher."""
    return [op for op in difflib.SequenceMatcher(None, a, b).get_opcodes() if op[0] != 'equal']


def paddle_hanja_support(c_seg: str, g_seg: str, paddle_hanja_set: set) -> tuple[str, str]:
    """반환: (Claude 측 한자 중 paddle이 지원하는 것, Gemini 측 동일)."""
    c_h = ''.join(ch for ch in c_seg if is_hanja(ch) and ch in paddle_hanja_set)
    g_h = ''.join(ch for ch in g_seg if is_hanja(ch) and ch in paddle_hanja_set)
    return c_h, g_h


# ============================================================
# Mode: analyze (단일 unit 상세)
# ============================================================

def mode_analyze(article_dir: Path, unit_id: str, engines: list[str]) -> None:
    paths = unit_paths(article_dir, unit_id, engines)
    texts = {n: load_clean(p) for n, p in paths.items()}
    print(f'=== {article_dir.name} / {unit_id}: 3-engine consensus analysis ===\n')

    print('## 1. Character class breakdown')
    print(f"{'engine':<16s}  total  hanja  hangul  jamo  ᄒᆞ_count")
    for name in engines:
        t = texts[name]
        s = stats(t)
        print(f"{name:<16s}  {s['total']:>5d}  {s['hanja']:>5d}  {s['hangul']:>6d}  {s['jamo']:>4d}  {s['arae_h']:>4d}")

    if 'claude_opus_4_7' not in texts or 'gemini' not in texts:
        print('\n(claude_opus_4_7 or gemini missing — skipping pairwise & diff analysis)')
        return

    c = texts['claude_opus_4_7']
    g = texts['gemini']
    p = texts.get('paddle', '')
    h_c, h_g, h_p = hanja_only(c), hanja_only(g), hanja_only(p)

    print('\n## 2. Hanja-only consensus')
    print(f'  Claude hanja ({len(h_c)} chars): {h_c}')
    print(f'  Gemini hanja ({len(h_g)} chars): {h_g}')
    print(f'  Paddle hanja ({len(h_p)} chars): {h_p}')

    sm_cg = difflib.SequenceMatcher(None, h_c, h_g)
    sm_cp = difflib.SequenceMatcher(None, h_c, h_p)
    sm_gp = difflib.SequenceMatcher(None, h_g, h_p)
    print('\n  Pairwise LCS-based ratio (1.0 = identical):')
    print(f'    Claude <-> Gemini: {sm_cg.ratio():.3f}')
    print(f'    Claude <-> Paddle: {sm_cp.ratio():.3f}')
    print(f'    Gemini <-> Paddle: {sm_gp.ratio():.3f}')

    # 3-way multiset intersection
    common = Counter(h_c) & Counter(h_g) & Counter(h_p)
    common_count = sum(common.values())
    print(f'\n  3-way hanja multiset intersection: {common_count} chars common to all 3 engines')

    print('\n## 3. Claude vs Gemini full-text diff (top 30 regions)')
    diffs = pairwise_diffs(c, g)
    print(f'  Total diff regions: {len(diffs)}')
    for tag, i1, i2, j1, j2 in diffs[:30]:
        print(f"    [{tag}]  C[{i1}:{i2}]={c[i1:i2]!r:<40s}  G[{j1}:{j2}]={g[j1:j2]!r}")

    print('\n## 4. Head/tail samples')
    for name in engines:
        t = texts[name]
        print(f'  {name} head[:60]: {t[:60]}')
    print()
    for name in engines:
        t = texts[name]
        print(f'  {name} tail[-60:]: {t[-60:]}')


# ============================================================
# Mode: all (article 전체 요약 표)
# ============================================================

def mode_all(article_dir: Path, units: list[dict], engines: list[str]) -> None:
    print(f'=== {article_dir.name}: all units summary ===\n')
    cols = engines.copy()
    header = f"{'unit':<22s}  " + '  '.join(f'{e[:6]:>6s}_t' for e in cols) + '  ' + '  '.join(f'{e[:6]:>6s}_h' for e in cols) + '  CG_LCS  3way_h  diff_n  C_ᄒᆞ  G_ᄒᆞ'
    print(header)
    for u in units:
        unit_id = u['id']
        paths = unit_paths(article_dir, unit_id, engines)
        texts = {n: load_clean(p) for n, p in paths.items()}
        c = texts.get('claude_opus_4_7', '')
        g = texts.get('gemini', '')
        p = texts.get('paddle', '')
        h_c, h_g, h_p = hanja_only(c), hanja_only(g), hanja_only(p)
        cg = difflib.SequenceMatcher(None, h_c, h_g).ratio() if h_c and h_g else 0.0
        common = Counter(h_c) & Counter(h_g) & Counter(h_p)
        common_count = sum(common.values())
        diff_n = len(pairwise_diffs(c, g))
        totals = '  '.join(f'{len(texts.get(e, "")):>8d}' for e in cols)
        hanjas = '  '.join(f'{len(hanja_only(texts.get(e, ""))):>8d}' for e in cols)
        print(f"{unit_id:<22s}  {totals}  {hanjas}  {cg:>6.3f}  {common_count:>6d}  {diff_n:>6d}  {c.count('ᄒᆞ'):>4d}  {g.count('ᄒᆞ'):>4d}")


# ============================================================
# Mode: review (단별 review_<unit>.md 산출)
# ============================================================

def build_review_md(unit_id: str, paths: dict[str, Path]) -> str:
    texts = {n: load_clean(p) for n, p in paths.items()}
    c = texts.get('claude_opus_4_7', '')
    g = texts.get('gemini', '')
    p = texts.get('paddle', '')
    diffs = pairwise_diffs(c, g)
    h_p_set = set(hanja_only(p))

    lines = [
        f'# Review: {unit_id}',
        '',
        f'- Claude length: {len(c)} chars',
        f'- Gemini length: {len(g)} chars',
        f'- Paddle hanja length: {len(hanja_only(p))} chars',
        f'- Diff regions (Claude vs Gemini): {len(diffs)}',
        '',
        '## Diff table',
        '',
        '| # | tag | Claude segment | Gemini segment | Paddle hanja support |',
        '|---|---|---|---|---|',
    ]
    for i, (tag, i1, i2, j1, j2) in enumerate(diffs, 1):
        c_seg = c[i1:i2]
        g_seg = g[j1:j2]
        votes = []
        for ch in c_seg:
            if is_hanja(ch) and ch in h_p_set:
                votes.append(f'C:{ch}')
        for ch in g_seg:
            if is_hanja(ch) and ch in h_p_set:
                votes.append(f'G:{ch}')
        v = ', '.join(votes) if votes else '-'
        c_disp = c_seg.replace('|', '\\|') if c_seg else '∅'
        g_disp = g_seg.replace('|', '\\|') if g_seg else '∅'
        lines.append(f'| {i} | {tag} | `{c_disp}` | `{g_disp}` | {v} |')

    lines.extend([
        '',
        '## Heads',
        f'- Claude: `{c[:80]}`',
        f'- Gemini: `{g[:80]}`',
        f'- Paddle: `{p[:80]}`',
    ])
    return '\n'.join(lines)


def mode_review(article_dir: Path, units: list[dict], engines: list[str]) -> None:
    out_dir = article_dir / 'ocr'
    out_dir.mkdir(parents=True, exist_ok=True)
    for u in units:
        unit_id = u['id']
        paths = unit_paths(article_dir, unit_id, engines)
        md = build_review_md(unit_id, paths)
        out_path = out_dir / f'review_{unit_id}.md'
        out_path.write_text(md + '\n', encoding='utf-8')
        print(f'wrote {out_path}')


# ============================================================
# Mode: draft ((2) 고충실본 draft v0 자동 초안)
# ============================================================

def build_unit_with_markers(paths: dict[str, Path]) -> tuple[str, int]:
    """Claude를 base로 ⚠️ 마커 인라인 삽입. 반환: (텍스트, diff 영역 수)."""
    texts = {n: load_clean(p) for n, p in paths.items()}
    c = texts.get('claude_opus_4_7', '')
    g = texts.get('gemini', '')
    p_hanja_set = set(hanja_only(texts.get('paddle', '')))

    if not c and not g:
        return '', 0
    if not c:
        return g, 0
    if not g:
        return c, 0

    sm = difflib.SequenceMatcher(None, c, g)
    out_parts = []
    n_diff = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            out_parts.append(c[i1:i2])
        else:
            n_diff += 1
            c_seg = c[i1:i2]
            g_seg = g[j1:j2]
            p_c, p_g = paddle_hanja_support(c_seg, g_seg, p_hanja_set)
            c_disp = c_seg if c_seg else '∅'
            g_disp = g_seg if g_seg else '∅'
            p_part = ''
            if p_c or p_g:
                p_part = f'|P:C={p_c or "-"};G={p_g or "-"}'
            marker = f'⚠️[C:{c_disp}|G:{g_disp}{p_part}]'
            out_parts.append(marker)
    return ''.join(out_parts), n_diff


def mode_draft(article_dir: Path, meta: dict, units: list[dict], engines: list[str]) -> None:
    article = meta.get('article', {})
    slug = article.get('slug', article_dir.name)
    title = article.get('title', '')
    author = article.get('author', '')
    journal = article.get('journal', '')
    issue_total = article.get('issue_total', '')
    pub_date = article.get('publication_date', '')
    section = article.get('section', '')

    body_parts = []
    diff_total = 0
    for u in units:
        unit_id = u['id']
        paths = unit_paths(article_dir, unit_id, engines)
        unit_text, n_diff = build_unit_with_markers(paths)
        diff_total += n_diff
        if unit_text:
            body_parts.append(unit_text)

    full_body = '\n\n'.join(body_parts)  # unit 간 빈 줄 — 인간이 단락 재구성
    unit_ids = [u['id'] for u in units]

    out_lines = [
        '---',
        'type: transcript',
        'fidelity: high  # 층위 (2) 고충실본',
        'status: draft_v0_auto_consensus  # ⚠️ 마커 해소 후 v1로 격상',
        f'units: [{", ".join(unit_ids)}]',
        f'article_slug: {slug}',
        f'article_title: {title}',
        f'author: {author}',
        f'journal_issue: {journal} 통권 {issue_total} ({pub_date})' if issue_total else f'journal_issue: {journal}',
        f'section: {section}',
        'created: 2026-05-09',
        f'updated: 2026-05-09 (auto-generated by consensus.py v1.0)',
        f'ocr_engines: [{", ".join(engines)}]',
        'consensus_policy: _design/2026-05-09_cheondogyo_wolbo_consensus_policy_v0_3.md',
        f'diff_regions_total: {diff_total}  # 인간 중재 대상 마커 수',
        '---',
        '',
        f'# {title} — (2) 고충실 전사본 (draft v0 auto)',
        '',
        f'본 초안은 3엔진 합의 분석으로 자동 생성. Claude(주 도구)를 base로, ',
        f'Claude·Gemini가 다른 영역에 ⚠️ 마커를 인라인 삽입했다. ',
        f'마커 총 {diff_total}건이 인간 중재 대상.',
        '',
        '## 본문',
        '',
    ]
    if section:
        out_lines.append(f'[section] {section}')
        out_lines.append('')
    if title:
        out_lines.append(f'[title] {title}')
        out_lines.append('')
    if author:
        out_lines.append(f'[author] {author}')
        out_lines.append('')
    out_lines.append('[body]')
    out_lines.append('')
    out_lines.append(full_body)
    out_lines.extend([
        '',
        '## ⚠️ 마커 해소 가이드',
        '',
        f'마커 형식: `⚠️[C:claude_seg|G:gemini_seg|P:C=…;G=…]`',
        '',
        '- C: Claude OCR 영역, G: Gemini OCR 영역, P: Paddle 한자 검증 지원',
        '- 한 쪽이 정확하면 마커 전체를 해당 텍스트로 교체',
        '- 양쪽 다 부정확하면 시각 대조 후 정확한 텍스트로 교체',
        '- ∅ 표기는 해당 엔진이 그 영역을 비워뒀음을 의미 (누락/추가 분쟁)',
        '',
        '해소 정책 (정책 v0.3 §1-16):',
        '- 한자 시각 유사자: Paddle 검증 + 의미 분석 (§12)',
        '- 옛한글 어미 자모: 시각 대조 권위 (§13)',
        '- Claude 본문 누락: Gemini cross-check 우세 (§14)',
        '- 어조사·어미 누락: 한문 어휘 사전 후보정 (§15)',
        '- 구조적 오인: 시각 대조 권위 (§16)',
        '',
        '모든 ⚠️ 마커 해소 후 `status: draft_v1`로 갱신, 파일명도 `.draft_v0` 제거.',
    ])

    out_dir = article_dir / 'transcripts'
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f'{article_dir.name}.high_fidelity.draft_v0.md'
    out_path.write_text('\n'.join(out_lines) + '\n', encoding='utf-8')
    print(f'wrote {out_path}')
    print(f'diff regions (⚠️ markers): {diff_total} across {len(body_parts)} units')


# ============================================================
# CLI
# ============================================================

def main() -> int:
    ap = argparse.ArgumentParser(
        description='Cheondogyo wolbo 3-engine consensus pipeline v1.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument('mode', choices=['analyze', 'all', 'review', 'draft'])
    ap.add_argument('--article', '-a', required=True,
                    help='article path or slug (e.g. 01_kwonyu_1911-01)')
    ap.add_argument('--unit', '-u',
                    help='unit id (required for analyze mode, e.g. unit_3_p2u)')
    ap.add_argument('--engines', '-e',
                    help='comma-separated engine list (default: auto-discover, gpt5 excluded)')
    args = ap.parse_args()

    article_dir = resolve_article_dir(args.article)
    meta = load_meta(article_dir)
    units = discover_units(meta)
    if not units:
        print(f'ERROR: no units in {article_dir / "meta.yaml"}', file=sys.stderr)
        return 1
    engines = args.engines.split(',') if args.engines else discover_engines(article_dir)
    if not engines:
        print(f'ERROR: no OCR engines found under {article_dir / "ocr"}', file=sys.stderr)
        return 1

    print(f'(article: {article_dir.relative_to(BASE)} | engines: {engines} | units: {len(units)})\n', file=sys.stderr)

    if args.mode == 'analyze':
        if not args.unit:
            print('ERROR: --unit required for analyze mode', file=sys.stderr)
            return 1
        mode_analyze(article_dir, args.unit, engines)
    elif args.mode == 'all':
        mode_all(article_dir, units, engines)
    elif args.mode == 'review':
        mode_review(article_dir, units, engines)
    elif args.mode == 'draft':
        mode_draft(article_dir, meta, units, engines)
    return 0


if __name__ == '__main__':
    sys.exit(main())
