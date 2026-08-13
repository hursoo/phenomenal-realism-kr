# -*- coding: utf-8 -*-
"""작업장에서 만든 것을 **저장소로 옮긴다** — 규칙대로, 빠뜨리지 않고.

세 곳의 역할

    raw(tnt)          내려받은 지면 원본. **손대지 않는다.** tnt의 제1 금기다.
    워크벤치(tnt)      파이프라인이 도는 작업장. `units/*.png`(2.2GB)와 중간 산출이 산다.
    저장소(공개)        내놓는 판. 지면 사본 + 판독 + 전사본 + 문서.

무엇을 옮기고 무엇을 안 옮기나

    ✅ meta.yaml · ocr/<engine>/*.txt · transcripts/*.md   — 공개본의 실체
    ✅ 정본 (wolbo54_review_workbench/*.high_fidelity.md)  — 작업장이 master다
    ✅ 지면 jpg (raw → source_pages/<슬러그>/)              — 판정의 최종 근거
    ❌ units/*.png                                        — 2.2GB. 지면에서 다시 자르면 된다
    ❌ raw 자체                                            — 원본은 tnt에 남는다
    ❌ ocr/gpt5, ocr/paddle                                — 시리즈에서 제외된 엔진

이름은 세 곳이 같다 — `NN_슬러그_YYYY-MM`. 어느 트리에서든 같은 이름으로 찾을 수 있어야
서로를 오갈 수 있다.

쓰기
    python3 sync_to_repo.py --dry-run          # 무엇이 옮겨질지만
    python3 sync_to_repo.py --series 87-157    # 새 편만
    python3 sync_to_repo.py --apply            # 전부
"""
import argparse
import filecmp
import re
import shutil
import sys
from pathlib import Path

import yaml

WB = Path('/home/creta/work/0_tnt/hyeonsang/_ocr_experiments/cheondogyo_wolbo_series')
RAW = Path('/home/creta/work/0_tnt/hyeonsang/raw/journals/cheondogyo_wolbo/'
           'nl_bibliography/articles')
REPO = Path(__file__).resolve().parents[2] / 'data' / '5_magazine_sources' / 'wolbo'

SKIP_ENGINES = {'gpt5', 'paddle'}


def parse_range(s):
    out = []
    for part in s.split(','):
        if '-' in part:
            a, b = part.split('-', 1)
            out += list(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return sorted(set(out))


def copy(src, dst, plan, apply_):
    """바뀐 것만 옮긴다. 같은 내용이면 건드리지 않는다."""
    if dst.exists() and filecmp.cmp(src, dst, shallow=False):
        return False
    plan.append((src, dst))
    if apply_:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--series', default='')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--with-pages', action='store_true', default=True,
                    help='지면 jpg도 옮긴다 (기본 켬)')
    args = ap.parse_args()
    apply_ = args.apply and not args.dry_run
    want = set(parse_range(args.series)) if args.series else None

    plan, pages, skipped = [], [], []
    for d in sorted((WB / 'articles').iterdir()):
        m = re.match(r'(\d+)_', d.name)
        if not (d.is_dir() and m):
            continue
        n = int(m.group(1))
        if want and n not in want:
            continue
        rd = REPO / 'articles' / d.name

        meta_p = d / 'meta.yaml'
        if not meta_p.exists():
            skipped.append(f'{d.name}: meta.yaml 없음')
            continue
        copy(meta_p, rd / 'meta.yaml', plan, apply_)

        # 전사본 — 초벌이 없으면 아직 판독 전이다
        drafts = sorted((d / 'transcripts').glob('*.md')) if (d / 'transcripts').is_dir() else []
        if not drafts:
            skipped.append(f'{d.name}: 전사본 없음 (판독 전)')
        for f in drafts:
            copy(f, rd / 'transcripts' / f.name, plan, apply_)

        for eng in sorted((d / 'ocr').iterdir()) if (d / 'ocr').is_dir() else []:
            if not eng.is_dir() or eng.name in SKIP_ENGINES:
                continue
            # .txt = 단위별 엔진 원출력 · .md = 영인·단일 판독본(단 단위 보고)
            for f in sorted(list(eng.glob('*.txt')) + list(eng.glob('*.md'))):
                copy(f, rd / 'ocr' / eng.name / f.name, plan, apply_)

        # 지면 — raw에서 저장소의 source_pages/<같은 이름>/으로
        if args.with_pages:
            meta = yaml.safe_load(meta_p.read_text(encoding='utf-8'))
            src = (meta.get('source_dir') or '').rstrip('/').split('/')[-1]
            pdir = RAW / src if (RAW / src).is_dir() else RAW / d.name
            sp = REPO / 'source_pages' / d.name
            if pdir.is_dir():
                for f in sorted(pdir.glob('*.jpg')):
                    if copy(f, sp / f.name, plan, apply_):
                        pages.append((f, sp / f.name))
                mj = pdir / 'meta.json'
                if mj.exists():
                    copy(mj, sp / 'meta.json', plan, apply_)
            else:
                skipped.append(f'{d.name}: raw 지면을 못 찾음')

    # 🔴 편 목록 자체를 안 옮기고 있었다. 그래서 저장소의 series_index.csv 가 86편에서
    #    멈춰 있었고, 그것을 읽는 build_reading.py 가 **읽기용 판을 86편만 만들었다.**
    #    지면·판독·전사본은 158편이 다 올라가 있는데 읽는 판만 없었다(2026-08-12 발견).
    for name in ('series_index.csv', 'series_index.md'):
        src = WB / name
        if src.exists():
            copy(src, REPO / name, plan, apply_)

    # 정본은 두 곳에 산다 — 작업장의 검수판과 저장소의 공개판.
    # 2026-08-12에 C34·C36 보완분이 저장소에만 들어가 둘이 갈라졌다.
    # **작업장이 master다**(Soo가 거기서 검수한다). 여기서 늘 맞춘다.
    vt_wb, vt_repo = WB / 'wolbo54_review_workbench', REPO / 'verified_transcripts'
    if vt_wb.is_dir() and vt_repo.is_dir():
        for f in sorted(vt_wb.glob('*.high_fidelity.md')):
            if copy(f, vt_repo / f.name, plan, apply_):
                print(f'  정본 갱신: {f.name}')

    npage = len(pages)
    print(f'옮길 파일 {len(plan)}개 (그 가운데 지면 {npage}장)')
    for s, dd in plan[:12]:
        print(f'  {dd.relative_to(REPO)}')
    if len(plan) > 12:
        print(f'  … 그 밖 {len(plan) - 12}개')
    if skipped:
        print(f'\n건너뛴 것 {len(skipped)}')
        for s in skipped[:12]:
            print(f'  {s}')
    if not apply_:
        print('\n--apply 를 주면 실제로 옮긴다')
    else:
        print('\n옮겼다. 저장소에서 git status로 확인하고 커밋한다.')
        print('⚠️ 단 이미지(units/*.png)는 옮기지 않았다 — 지면에서 다시 자르면 된다.')


if __name__ == '__main__':
    main()
