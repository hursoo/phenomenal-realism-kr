# -*- coding: utf-8 -*-
"""글줄 단위 4배 재판독을 **어디부터** 걸지 정한다 — 깔끔하게 잘린 단부터.

왜 순서가 필요한가
    글줄 재판독은 컬럼당 1회다. 한 편이 80~100회, 코퍼스 전체는 만 회가 넘는다.
    전편에 돌릴 것이 못 되므로 **값이 가장 큰 곳부터** 걸어야 한다.

    그런데 값이 큰 곳은 「중요한 편」이 아니라 **잘 잘린 단**이다. 잘못 잘린 단을
    4배로 확대해 봐야 없는 글자가 생기지 않는다 — 오히려 옆 단 글자를 제 것인 양
    또렷하게 읽어 **틀린 판독에 확신만 얹는다.** 그래서 선별이 먼저다.

무엇을 보나 (단마다)

    구분선     지면의 구분선을 검출해 잘랐나(`divider_detected`), 아니면 고정값인가
    가장자리   위·아래 가장자리에 걸려 잘린 글자 상자가 있나(`detect_cut_glyphs`)
    글줄       컬럼이 몇 개 잡히나, 폭이 고른가 (들쭉날쭉하면 검출이 흔들린 것)
    빈 판독    두 엔진 가운데 아무것도 못 읽은 쪽이 있나

    이 넷으로 **깔끔함 점수**를 매긴다. 점수가 높을수록 4배 재판독의 값이 크다.

    ⚠️ 점수는 **이미지가 깔끔한가**만 본다. 그 편이 연구에 중요한가는 사람이 정한다.
    그래서 산출에 `series`를 남긴다 — 정본화 대상 편을 먼저 고르고, 그 안에서 이
    점수로 단의 차례를 정하는 것이 옳은 쓰임이다.

쓰기
    python3 rank_units_for_reread.py <articles_root> --out reread_worklist.csv
    python3 rank_units_for_reread.py <articles_root> --min 87 --max 157
"""
import argparse
import csv
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from detect_cut_glyphs import analyze                          # noqa: E402


def col_stats(png):
    hits, ncols, size = analyze(png)
    return hits, ncols, size


def engine_empty(adir, unit):
    """**있는데 비어 있는** 판독만 센다. 파일이 아직 없는 것은 판독 전이지 흠이 아니다."""
    out = []
    for eng in ('claude_opus_4_7', 'gemini'):
        f = adir / 'ocr' / eng / f'{unit}.txt'
        if not f.exists():
            continue
        t = f.read_text(encoding='utf-8', errors='ignore')
        if not re.search(r'\[col\s*\d+\]\s*\S', t):
            out.append(eng)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('articles_root')
    ap.add_argument('--min', type=int, default=0)
    ap.add_argument('--max', type=int, default=9999)
    ap.add_argument('--out', default='')
    args = ap.parse_args()

    root = Path(args.articles_root)
    rows = []
    for d in sorted(root.iterdir()):
        m = re.match(r'(\d+)_', d.name)
        if not (d.is_dir() and m and (d / 'meta.yaml').exists()):
            continue
        n = int(m.group(1))
        if not (args.min <= n <= args.max):
            continue
        meta = yaml.safe_load((d / 'meta.yaml').read_text(encoding='utf-8'))
        det = {u.get('id'): u.get('divider_detected') for u in (meta.get('units') or [])}
        ovl = {u.get('id'): u.get('overlap') for u in (meta.get('units') or [])}
        for png in sorted((d / 'units').glob('*.png')):
            try:
                hits, ncols, size = col_stats(png)
            except Exception as e:                              # noqa: BLE001
                print(f'  ⚠ {d.name}/{png.stem}: {e}', file=sys.stderr)
                continue
            empty = engine_empty(d, png.stem)
            detected = det.get(png.stem)
            # 깔끔함 — 100에서 흠을 뺀다
            score = 100
            if not detected:
                score -= 25                       # 고정값으로 잘린 단
            # 겹쳐 자른 단은 가장자리에 조각이 남는 것이 **정상**이다 — 그러라고 겹쳤다.
            # 겹치지 않은 단에서만 가장자리 조각을 흠으로 센다.
            if not ovl.get(png.stem):
                score -= min(30, len(hits) * 5)
            if ncols < 4:
                score -= 20                       # 글줄이 너무 적게 잡혔다
            score -= 15 * len(empty)              # 엔진이 못 읽은 단
            rows.append(dict(
                series=n, article=d.name, unit=png.stem,
                size=f'{size[0]}x{size[1]}', cols=ncols,
                edge_cuts=len(hits),
                divider='검출' if detected else '고정값',
                overlap=ovl.get(png.stem) or 0,
                empty_engines=','.join(empty),
                score=max(0, score)))

    rows.sort(key=lambda r: (-r['score'], r['series'], r['unit']))
    print(f'단 {len(rows)}개 평가')
    if rows:
        good = [r for r in rows if r['score'] >= 85]
        mid = [r for r in rows if 60 <= r['score'] < 85]
        bad = [r for r in rows if r['score'] < 60]
        print(f'  85점 이상(깔끔) {len(good)} · 60~84 {len(mid)} · 60 미만(먼저 다시 잘라야) {len(bad)}')
        print(f'  글줄 합계 {sum(r["cols"] for r in rows)} '
              f'· 85점 이상만 {sum(r["cols"] for r in good)}')
        print('\n85점 미만이 많은 편 (다시 자르기 후보)')
        by = {}
        for r in rows:
            if r['score'] < 85:
                by[r['article']] = by.get(r['article'], 0) + 1
        for a, c in sorted(by.items(), key=lambda x: -x[1])[:10]:
            print(f'  {a:<24} {c}단')
    if args.out and rows:
        with open(args.out, 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader(); w.writerows(rows)
        print(f'\n→ {args.out}')
        print('별도 세션에서 이렇게 쓴다:')
        print('  python3 scripts/06_magazines/reread_columns.py <article_dir> --scale 4')
        print('  (worklist의 score 높은 단부터. 편 단위로 돌리려면 article 열을 쓴다)')


if __name__ == '__main__':
    main()
