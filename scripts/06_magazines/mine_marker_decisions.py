# -*- coding: utf-8 -*-
"""정본과 초벌을 정렬해 마커별 확정값을 뽑아 「결정 대장」을 만든다.

무엇을 하나
    검수를 마친 편은 초벌(`*.high_fidelity.draft_v0.md`)과 정본(`*.high_fidelity.md`)이
    짝으로 남아 있다. 초벌에는 엔진이 갈린 자리가 `⚠️[C:…|G:…]`로 보존돼 있으므로,
    둘을 정렬하면 **「이렇게 갈렸을 때 사람은 이렇게 정했다」**를 마커마다 뽑을 수 있다.
    그 표가 이후 자동 해소의 정답지가 된다.

한계 (중요)
    정본은 「둘 중 하나 고르기」의 산물이 아니라 **고르기 + 일괄 정규화(아래아·정자표)
    + 구조 선분리**의 합성물이다. 그래서 확정값이 두 후보 어느 쪽과도 다른 경우가
    3할쯤 나온다(`verdict=제3안`). 정렬 앵커를 4에서 12까지 올려도 이 비율은
    거의 변하지 않으므로 정렬 잡음이 아니라 실제 현상이다.
    A/B 택일의 채점에 쓸 수 있는 것은 `verdict`가 C 또는 G인 행뿐이다.

산출
    data/5_magazine_sources/wolbo/marker_decisions.csv


방법
  1. 초벌의 마커를 C쪽으로 펴서 cUnfold를 만들고, 각 마커가 cUnfold의
     어느 구간을 차지하는지 기록한다.
  2. cUnfold와 정본을 difflib으로 정렬한다.
  3. 마커 구간의 좌우에 **정확히 붙은 일치 블록**이 각각 ANCHOR자 이상이면
     그 사이의 정본 문자열을 확정값으로 본다. 아니면 포기한다(정밀도 우선).
"""
import re, difflib, sys, json
from pathlib import Path
from collections import Counter

WOLBO = Path(__file__).resolve().parents[2] / 'data' / '5_magazine_sources' / 'wolbo'
MK = re.compile(r'⚠️\[C:(.*?)\|G:(.*?)(?:\|P:[^\]]*)?\]')
ANCHOR = int(sys.argv[1]) if len(sys.argv) > 1 else 4


def strip_gold(s):
    s = re.sub(r'^---.*?\n---\n', '', s, flags=re.S)
    s = re.sub(r'\[unit:[^\]]*\]', '', s)
    s = re.sub(r'<\d+>', '', s)
    s = re.sub(r'^#.*$', '', s, flags=re.M)
    s = re.sub(r'\[body\]|\[/body\]', '', s)
    return re.sub(r'\s+', '', s)


def strip_draft_literal(s):
    s = re.sub(r'^---.*?\n---\n', '', s, flags=re.S)
    s = re.sub(r'^#.*$', '', s, flags=re.M)
    s = re.sub(r'\[body\]|\[/body\]', '', s)
    s = re.sub(r'\[unit:[^\]]*\]', '', s)
    s = re.sub(r'<\d+>', '', s)
    return s


def unfold_with_map(draft):
    """C쪽으로 편 문자열과, 마커별 (start,end,c,g)를 돌려준다."""
    out, spans, last = [], [], 0
    cur = 0
    for m in MK.finditer(draft):
        lit = re.sub(r'\s+', '', draft[last:m.start()])
        out.append(lit); cur += len(lit)
        c, g = m.group(1), m.group(2).split('|P:')[0]
        cv = '' if c == '∅' else re.sub(r'\s+', '', c)
        out.append(cv)
        spans.append((cur, cur + len(cv), c, g, len(spans)))
        cur += len(cv); last = m.end()
    lit = re.sub(r'\s+', '', draft[last:])
    out.append(lit)
    return ''.join(out), spans


def mine(slug, draft_path, gold_path):
    draft = strip_draft_literal(draft_path.read_text(encoding='utf-8', errors='ignore'))
    gold = strip_gold(gold_path.read_text(encoding='utf-8', errors='ignore'))
    cu, spans = unfold_with_map(draft)

    sm = difflib.SequenceMatcher(None, cu, gold, autojunk=False)
    blocks = [b for b in sm.get_matching_blocks() if b.size > 0]

    def map_left(p):
        """p 바로 앞이 ANCHOR자 이상 일치할 때만 gold 위치를 준다."""
        for b in blocks:
            if b.a <= p <= b.a + b.size and (p - b.a) >= ANCHOR:
                return b.b + (p - b.a)
        return None

    def map_right(p):
        """p 바로 뒤가 ANCHOR자 이상 일치할 때만."""
        for b in blocks:
            if b.a <= p <= b.a + b.size and (b.a + b.size - p) >= ANCHOR:
                return b.b + (p - b.a)
        return None

    rows, miss = [], 0
    for s, e, c, g, mi in spans:
        gs, ge = map_left(s), map_right(e)
        if gs is None or ge is None or ge < gs:
            miss += 1
            continue
        final = gold[gs:ge]
        cv = '' if c == '∅' else c
        gv = '' if g == '∅' else g
        verdict = ('C' if final == cv else 'G' if final == gv else
                   '삭제' if final == '' else '제3안')
        rows.append(dict(slug=slug, mi=mi, c=c, g=g, final=final, verdict=verdict,
                         ctx=gold[max(0, gs - 8):gs] + '⟪' + final + '⟫' + gold[ge:ge + 8]))
    return rows, miss


def main():
    allrows, tot_miss, tot = [], 0, 0
    jobs = []
    for p in sorted(WOLBO.glob('verified_transcripts/*.high_fidelity.md')):
        slug = p.name.split('.')[0]
        d = list((WOLBO / 'articles' / slug / 'transcripts').glob('*draft_v0.md'))
        if d: jobs.append((slug, d[0], p))
    c01d = list((WOLBO / 'articles' / '001_勸誘_1911-01' / 'transcripts').glob('*draft_v0.md'))
    c01g = WOLBO / 'articles/001_勸誘_1911-01/transcripts/article_01.high_fidelity.md'
    if c01d and c01g.exists(): jobs.append(('001_勸誘_1911-01', c01d[0], c01g))

    for slug, dp, gp in jobs:
        rows, miss = mine(slug, dp, gp)
        n = len(rows) + miss
        tot += n; tot_miss += miss; allrows += rows
        vc = Counter(r['verdict'] for r in rows)
        print(f"{slug:<22} 마커{n:>4}  대장확보{len(rows):>4} ({len(rows)/n*100:4.1f}%)  "
              f"C{vc['C']:>4} G{vc['G']:>3} 제3안{vc['제3안']:>3} 삭제{vc['삭제']:>3}")

    print(f"\n합계 마커 {tot} · 대장 확보 {len(allrows)} ({len(allrows)/tot*100:.1f}%) · 포기 {tot_miss}")
    vc = Counter(r['verdict'] for r in allrows)
    print('판정 분포:', dict(vc))
    import csv
    out = WOLBO / 'marker_decisions.csv'
    with open(out, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['article', 'marker_index', 'claude', 'gemini', 'final', 'verdict', 'context'])
        for r in sorted(allrows, key=lambda r: (r['slug'], r['mi'])):
            w.writerow([r['slug'], r['mi'], r['c'], r['g'], r['final'], r['verdict'], r['ctx']])
    print('→', out)


main()
