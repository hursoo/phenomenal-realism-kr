# -*- coding: utf-8 -*-
"""글줄 4배 재판독을 **어느 편에** 걸지 고른다 — 깔끔함 × 나쁨.

왜 둘을 곱하나
    글줄 재판독은 컬럼당 1회다. 158편이면 만 삼천 회가 넘으니 전편에 걸 것이 못 된다.
    그래서 고르는데, **「나쁜 편부터」가 곧바로 답이 되지 않는다.**

    `rank_units_for_reread.py`가 이미 적어 둔 경고가 있다 —

        잘못 잘린 단을 4배로 확대해 봐야 없는 글자가 생기지 않는다.
        오히려 옆 단 글자를 제 것인 양 또렷하게 읽어 **틀린 판독에 확신만 얹는다.**

    곧 값이 큰 자리는 **깔끔하게 잘렸는데 판독이 나쁜 편**이다. 깔끔하지 않으면 확대가
    해롭고, 판독이 이미 좋으면 확대가 남는 게 없다. 그래서 둘을 곱한다.

        깔끔함 — 구분선을 검출해 잘랐나, 가장자리에 걸린 글자가 없나, 빈 판독이 없나
        나쁨   — 마커가 얼마나 촘촘한가, 그 가운데 대분기(≥15자)가 몇인가

무엇을 세나
    나쁨은 **글줄당 마커 수**로 잰다. 마커 총수로 재면 긴 편이 무조건 이긴다 —
    긴 것과 나쁜 것은 다르다. 대분기는 두 엔진이 아예 다른 것을 본 자리이므로
    따로 가중한다.

쓰기
    python3 select_reread_targets.py --top 30
    python3 select_reread_targets.py --top 30 --min 1 --max 86
"""
import argparse
import csv
import re
from pathlib import Path

import yaml

WB = Path('/home/creta/work/0_tnt/hyeonsang/_ocr_experiments/cheondogyo_wolbo_series')
REPO = Path(__file__).resolve().parents[2] / 'data' / '5_magazine_sources' / 'wolbo'
MARKER = re.compile(r'⚠️\[C:(.*?)\|G:(.*?)(?:\|P:[^\]]*)?\]')


def stats(adir):
    """전사본에서 마커를, meta에서 깔끔함을 읽는다."""
    tdir = adir / 'transcripts'
    fs = sorted(tdir.glob('*draft_v0.md')) if tdir.is_dir() else []
    if not fs:
        return None
    t = fs[0].read_text(encoding='utf-8', errors='ignore')
    i = t.find('[body]')
    body = t[i:] if i >= 0 else t
    ms = MARKER.findall(body)
    big = sum(1 for c, g in ms if max(len(c), len(g)) >= 15)

    meta = yaml.safe_load((adir / 'meta.yaml').read_text(encoding='utf-8'))
    units = meta.get('units') or []
    det = sum(1 for u in units if u.get('divider_detected'))
    # 한 면이 통째로 한 단인 편은 애초에 가를 것이 없으니 깔끔한 것으로 본다
    whole = sum(1 for u in units if not re.search(r'_p\d+[ul]', u.get('file', '')))
    clean = (det + whole) / len(units) if units else 0

    empty = 0
    if (adir / 'ocr').is_dir():
        for e in (adir / 'ocr').iterdir():
            if not e.is_dir() or e.name.startswith('_') or e.name in ('gpt5', 'paddle'):
                continue
            for f in e.glob('*.txt'):
                if not re.search(r'\[col\s*\d+\]\s*\S',
                                 f.read_text(encoding='utf-8', errors='ignore')):
                    empty += 1
    return {'markers': len(ms), 'big': big, 'units': len(units),
            'clean': clean, 'empty': empty}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--top', type=int, default=30)
    ap.add_argument('--min', type=int, default=0)
    ap.add_argument('--max', type=int, default=9999)
    args = ap.parse_args()

    rows = []
    for d in sorted((WB / 'articles').iterdir()):
        m = re.match(r'(\d+)_', d.name)
        if not (d.is_dir() and m and (d / 'meta.yaml').exists()):
            continue
        n = int(m.group(1))
        if not (args.min <= n <= args.max):
            continue
        s = stats(d)
        if not s or not s['units']:
            continue
        # 나쁨 — 단당 마커. 긴 편이 무조건 이기지 않도록 길이로 나눈다
        bad = s['markers'] / s['units'] + 2.0 * s['big'] / s['units']
        # 깔끔함 — 빈 판독이 있으면 깎는다
        clean = s['clean'] * (0.5 if s['empty'] else 1.0)
        rows.append({'series': n, 'slug': d.name, **s,
                     'bad_per_unit': round(bad, 2), 'clean': round(clean, 2),
                     'score': round(bad * clean, 2)})

    rows.sort(key=lambda r: -r['score'])
    out = REPO / 'reread_targets.csv'
    with out.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    top = rows[:args.top]
    print(f'{len(rows)}편 가운데 상위 {len(top)}편 — 깔끔함 × 나쁨')
    print(f"{'편':>4} {'슬러그':<24} {'단':>3} {'마커':>5} {'대분기':>5} "
          f"{'단당':>6} {'깔끔':>5} {'점수':>6}")
    for r in top:
        print(f"{r['series']:>4} {r['slug'][:24]:<24} {r['units']:>3} {r['markers']:>5} "
              f"{r['big']:>5} {r['bad_per_unit']:>6} {r['clean']:>5} {r['score']:>6}")
    print(f'\n{out}')
    print('상위 편 목록: ' + ','.join(str(r['series']) for r in top))


if __name__ == '__main__':
    main()
