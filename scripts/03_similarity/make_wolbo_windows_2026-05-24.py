"""월보 토큰을 28 고유토큰 윈도우로 재분할 → tokens_월보_win.csv (2026-05-24).

부록 C.5 명세 그대로(TARGET=28, 잔여 고유 ≥10이면 독립 윈도우·미만이면 직전 병합).
입력 tokens_월보.csv의 행 순서 = 문서 순서(글 안). 출력 스키마는 입력과 동일
(src, n_chunk_id, c, token)이되 n_chunk_id = '<글>-W<nn>', 윈도우당 고유 토큰만 1행씩.

목적: 헤드라인 재산출(개벽·단행본은 5문장 묶음 유지, 월보만 토큰 윈도우)을 위해
월보를 개벽 청크와 같은 단위 자릿수로 맞춘 토큰 파일을 만든다.
"""
import csv
import sys
from collections import defaultdict, OrderedDict
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
NORM = Path(r'C:\hp_data\0_tnt\hyeonsang\_ocr_experiments\unified_db_2026-05-19\output\norm')
TARGET, MIN_TAIL = 28, 10


def windows(tokens):
    """문서 순서 토큰열 → 고유토큰 ~28 윈도우(집합) 리스트. C.5 규약."""
    out, cur = [], set()
    for t in tokens:
        cur.add(t)
        if len(cur) >= TARGET:
            out.append(set(cur))
            cur = set()
    if cur:
        if len(cur) >= MIN_TAIL or not out:
            out.append(set(cur))
        else:
            out[-1] |= cur
    return out


def main():
    # 글별 문서 순서 토큰열(중복 보존)
    seq = OrderedDict()
    with open(NORM / 'tokens_월보.csv', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            nid, tok = r['n_chunk_id'], r['token']
            if not nid or not tok:
                continue
            art = nid.split('-')[0]
            seq.setdefault(art, []).append(tok)

    out_rows = []
    n_win = 0
    for art, toks in seq.items():
        for wi, s in enumerate(windows(toks), 1):
            wid = f'{art}-W{wi:02d}'
            n_win += 1
            for tok in sorted(s):
                out_rows.append(('월보', wid, art, tok))

    outp = NORM / 'tokens_월보_win.csv'
    with outp.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['src', 'n_chunk_id', 'c', 'token'])
        w.writerows(out_rows)

    sizes = sorted(len(s) for toks in seq.values() for s in windows(toks))
    print(f'월보 글 {len(seq)}편 → 윈도우 {n_win}개 (토큰 행 {len(out_rows)})')
    print(f'윈도우 고유토큰 중앙값 {sizes[len(sizes)//2]} · min {sizes[0]} · max {sizes[-1]}')
    print(f'출력: {outp}')


if __name__ == '__main__':
    main()
