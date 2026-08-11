"""edge1_full_norm_2026-05-23.py의 월보-윈도우 변형 (2026-05-24).

방법 동일(바닥 없는 raw 자카드, 도달 분포·Cliff's δ·Top-K). 월보만 tokens_월보_win.csv
(28 고유토큰 윈도우)에서 읽고, 개벽·1915·1924는 기존 5문장 묶음 그대로.
"""
import csv
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
NORM = Path(r'C:\hp_data\0_tnt\hyeonsang\_ocr_experiments\unified_db_2026-05-19\output\norm')
FILE = {
    '1915': NORM / 'tokens_1915.csv',
    '1924': NORM / 'tokens_1924.csv',
    '개벽': NORM / 'tokens_개벽.csv',
    '월보': NORM / 'tokens_월보_win.csv',
}
_EMPTY = frozenset()


def load_bundles(src):
    bc = defaultdict(set)
    with open(FILE[src], encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            if r['n_chunk_id'] and r['token']:
                bc[r['n_chunk_id']].add(r['token'])
    return [s for s in bc.values() if s]


def inv_index(bundles):
    inv = defaultdict(set)
    for i, s in enumerate(bundles):
        for t in s:
            inv[t].add(i)
    return inv


def arrival(src_bundles, tgt_bundles, inv):
    out = []
    for s in src_bundles:
        cand = set()
        for t in s:
            cand |= inv.get(t, _EMPTY)
        bj = 0.0
        for i in cand:
            t = tgt_bundles[i]
            j = len(s & t) / len(s | t)
            if j > bj:
                bj = j
        out.append(bj)
    return out


def cliffs_delta(x, y):
    ys = sorted(y)
    import bisect
    n = len(ys)
    gt = lt = 0
    for xi in x:
        gt += bisect.bisect_left(ys, xi)
        lt += n - bisect.bisect_right(ys, xi)
    return (gt - lt) / (len(x) * len(y))


def pct(v, q):
    s = sorted(v)
    return s[int(round(q / 100 * (len(s) - 1)))]


def main():
    b1915 = load_bundles('1915')
    b1924 = load_bundles('1924')
    gb = load_bundles('개벽')
    wb = load_bundles('월보')
    mag = gb + wb
    inv24 = inv_index(b1924)
    print(f'모집단(월보-윈도우): 1915={len(b1915)} 1924={len(b1924)} '
          f'잡지={len(mag)} (개벽 {len(gb)} + 월보윈도우 {len(wb)})')

    npairs = len(b1915) * len(b1924)
    nonzero = 0
    mx = 0.0
    for s in b1915:
        cand = set()
        for t in s:
            cand |= inv24.get(t, _EMPTY)
        for i in cand:
            t = b1924[i]
            j = len(s & t) / len(s | t)
            if j > 0:
                nonzero += 1
                if j > mx:
                    mx = j
    print(f'\n[직접 N×N] {len(b1915)}×{len(b1924)} = {npairs:,} 짝')
    print(f'   비영(非零) {nonzero:,} = {nonzero/npairs*100:.1f}% | 전체 max={mx:.4f}')

    direct = arrival(b1915, b1924, inv24)
    mediated = arrival(mag, b1924, inv24)
    med_gb = arrival(gb, b1924, inv24)
    med_wb = arrival(wb, b1924, inv24)
    for name, v in (('직접 도달(1915→1924)', direct),
                    ('매개 도달(잡지→1924)', mediated),
                    ('  └ 개벽만', med_gb), ('  └ 월보윈도우만', med_wb)):
        print(f'\n[{name}] n={len(v)} mean={st.mean(v):.4f} median={st.median(v):.4f} '
              f'max={max(v):.4f} | p90/95/99 = {pct(v,90):.4f}/{pct(v,95):.4f}/{pct(v,99):.4f}')

    d = cliffs_delta(mediated, direct)
    print(f"\nCliff's δ (매개 vs 직접 도달) = {d:+.4f}")

    ds, ms = sorted(direct, reverse=True), sorted(mediated, reverse=True)
    print('\n=== Top-K (매개/직접) ===')
    for k in (10, 50, 100):
        dm, mm = st.mean(ds[:k]), st.mean(ms[:k])
        print(f'  K={k:>3}: 직접 {dm:.4f} | 매개 {mm:.4f} | 비율 {mm/dm:.2f}x')


if __name__ == '__main__':
    main()
