"""compute_jaccard_topk_norm_2026-05-23.py의 월보-윈도우 변형 (2026-05-24).

연산·파라미터 100% 동일(top-5-mean K=5, MIN_SHARED=2, 묶음별 F1, best-match 자카드).
단 하나만 바뀐다: 월보 토큰을 tokens_월보_win.csv(28 고유토큰 윈도우)에서 읽는다.
개벽·1915·1924는 기존 tokens_*.csv(5문장 묶음) 그대로.

목적: 헤드라인 매개 클러스터 순위·z를 월보가 개벽과 동일 단위일 때 재확인
      (단위 비등가성 한계를 발생 지점에서 제거).
산출: output/jaccard_topk5_wbwin_2026-05-24.csv
"""
import csv
import json
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

import openpyxl

sys.stdout.reconfigure(encoding='utf-8')
OUT = Path(r'C:\hp_data\0_tnt\hyeonsang\_ocr_experiments\unified_db_2026-05-19\output')
NORM = OUT / 'norm'
XLSX = {
    '1915': OUT / 'BK_IT_1915_PR_v1.4.xlsx',
    '1924': OUT / 'BK_YD_1924_IY_v1.3.xlsx',
    '개벽': OUT / 'MA_YD_10-20_GB.xlsx',
    '월보': OUT / 'MA_YD_10-20_WB.xlsx',
}
TOK = {  # 월보만 윈도우 파일, 나머지는 기존 묶음 파일
    '1915': NORM / 'tokens_1915.csv',
    '1924': NORM / 'tokens_1924.csv',
    '개벽': NORM / 'tokens_개벽.csv',
    '월보': NORM / 'tokens_월보_win.csv',
}
SRCS = ['1915', '1924', '개벽', '월보']
K = 5
MIN_SHARED = 2
CLUSTER = {('개벽', c) for c in ('C53', 'C43', 'C22', 'C19', 'C23')}
_EMPTY = frozenset()


def load_tokens_norm(src):
    by_chunk = defaultdict(set)
    with open(TOK[src], encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            nid, t = r['n_chunk_id'], r['token']
            if nid and t:
                by_chunk[nid].add(t)
    by_c = defaultdict(list)
    for nid, s in by_chunk.items():
        if s:
            by_c[nid.split('-')[0]].append(s)
    return dict(by_c)


def load_meta(path):
    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    h = list(rows[0])
    if 'src_metadata' not in h or 'local_id' not in h:
        return {}
    lid, mc = h.index('local_id'), h.index('src_metadata')
    meta = {}
    for r in rows[1:]:
        li = r[lid]
        if li and '-' in li and r[mc]:
            c = li.split('-')[0]
            if c not in meta:
                try:
                    meta[c] = json.loads(r[mc])
                except Exception:
                    pass
    return meta


def build_index(bundles):
    inv = defaultdict(set)
    for i, s in enumerate(bundles):
        for t in s:
            inv[t].add(i)
    return inv


def best_matches(src_bundles, tgt_bundles, inv):
    out = []
    for s in src_bundles:
        cand = set()
        for t in s:
            cand |= inv.get(t, _EMPTY)
        bj = 0.0
        for i in cand:
            t = tgt_bundles[i]
            inter = len(s & t)
            if inter < MIN_SHARED:
                continue
            j = inter / len(s | t)
            if j > bj:
                bj = j
        out.append(bj)
    return out


def topk_mean(vals, k=K):
    if not vals:
        return 0.0
    return st.mean(sorted(vals, reverse=True)[:k])


def f1(a, b):
    return 2 * a * b / (a + b) if a > 0 and b > 0 else 0.0


def main():
    by_c = {src: load_tokens_norm(src) for src in SRCS}
    meta = {src: load_meta(XLSX[src]) for src in SRCS}
    bundles = {src: [b for chs in by_c[src].values() for b in chs] for src in SRCS}
    print(f'[월보-윈도우] K={K}, MIN_SHARED={MIN_SHARED}  묶음/윈도우 수:',
          {s: len(b) for s, b in bundles.items()})
    inv1915, inv1924 = build_index(bundles['1915']), build_index(bundles['1924'])

    recs = []
    for src in SRCS:
        for c, chs in by_c[src].items():
            b15 = best_matches(chs, bundles['1915'], inv1915) if src != '1915' else None
            b24 = best_matches(chs, bundles['1924'], inv1924) if src != '1924' else None
            m = meta[src].get(c, {})
            rec = {
                'src': src, 'c': c, 'n': len(chs),
                'date': (m.get('publish_date') or '')[:10],
                'title': (m.get('title') or '')[:60],
                'edge2_top5': topk_mean(b15) if b15 is not None else '',
                'edge3_top5': topk_mean(b24) if b24 is not None else '',
            }
            if b15 is not None and b24 is not None:
                fvals = [f1(j15, j24) for j15, j24 in zip(b15, b24)]
                rec['f1_top5'] = topk_mean(fvals)
            else:
                rec['f1_top5'] = ''
            recs.append(rec)

    cols = ['src', 'c', 'n', 'date', 'edge2_top5', 'edge3_top5', 'f1_top5', 'title']
    outp = OUT / 'jaccard_topk5_wbwin_2026-05-24.csv'
    with outp.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in recs:
            w.writerow({k: r[k] for k in cols})
    print(f'CSV: {outp}')

    mags = [r for r in recs if r['src'] in ('개벽', '월보') and r['f1_top5'] != '']
    fvals = [r['f1_top5'] for r in mags]
    mu, sd = st.mean(fvals), st.stdev(fvals)
    ranked = sorted(mags, key=lambda x: -x['f1_top5'])
    rank = {(r['src'], r['c']): i for i, r in enumerate(ranked, 1)}
    print(f'\n=== 잡지 f1_top5 분포: n={len(mags)} mean={mu:.4f} sd={sd:.4f} max={max(fvals):.4f} ===')
    print('상위 12 글/윈도우-집계 (◆=매개 클러스터):')
    for i, r in enumerate(ranked[:12], 1):
        mk = '◆' if (r['src'], r['c']) in CLUSTER else ' '
        z = (r['f1_top5'] - mu) / sd
        print(f'  {i:>2}.{mk}{r["src"]:>3} {r["c"]:>4} N={r["n"]:>2} f1={r["f1_top5"]:.4f} z={z:+.2f} {r["date"]:10} {r["title"][:34]}')
    print('\n매개 클러스터 5편 순위·z:')
    for s, c in sorted(CLUSTER, key=lambda k: rank.get(k, 999)):
        r = next(x for x in mags if (x['src'], x['c']) == (s, c))
        z = (r['f1_top5'] - mu) / sd
        print(f'  {c}: f1={r["f1_top5"]:.4f} z={z:+.2f} 순위 {rank[(s, c)]}/{len(mags)}')

    # 월보 글 중 최상위(윈도우 집계 후) — C72 추적
    wb = sorted([r for r in mags if r['src'] == '월보'], key=lambda x: -x['f1_top5'])
    print('\n=== 월보 글 f1_top5 상위 6 (윈도우→글 top-5-mean) ===')
    for r in wb[:6]:
        z = (r['f1_top5'] - mu) / sd
        print(f'  {r["c"]:>4} N={r["n"]:>2} f1={r["f1_top5"]:.4f} z={z:+.2f} 순위 {rank[("월보", r["c"])]}/{len(mags)} {r["date"]:10} {r["title"][:30]}')


if __name__ == '__main__':
    main()
