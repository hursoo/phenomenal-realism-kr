# -*- coding: utf-8 -*-
"""직접 1915↔1924 닻 분석 — 5문장 묶음 단위(2월 워크숍의 문단 분석을 정본 묶음으로 재현).

(가) 직접 묶음 짝(자카드≥0.1) 분포·상위 짝·착지 장/절/항.
(나) 哲學 기표 묶음-단위 빈도(1915 vs 1924) + 참조밀도↔哲學 역상관(항 단위).
소스: norm/tokens_1915.csv · tokens_1924.csv (둘 다 5문장 묶음, 월보 윈도우 무관).
"""
import sys, csv, re
from collections import defaultdict
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")

NORM = Path(r"C:\hp_data\0_tnt\hyeonsang\_ocr_experiments\unified_db_2026-05-19\output\norm")
THR = 0.10
PHIL = {"哲學", "철학"}
# 노이즈 stoplist (2월 보고서 기준: 서수 + 범용어)
STOP = {"第一","第二","第三","第四","第五","第六","第七","第八","第九","第十",
        "宇宙","世界","如何","對照","區別"}

def load(fn):
    """chunk_id -> token set (set 기반, 빈 id 제외). 멀티셋 카운트도 반환."""
    sets = defaultdict(set); mult = defaultdict(int)
    with open(NORM / fn, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            cid, tok = r["n_chunk_id"], r["token"]
            if cid and tok:
                sets[cid].add(tok)
                mult[tok] += 1
    return sets, mult

s15, m15 = load("tokens_1915.csv")
s24, m24 = load("tokens_1924.csv")

inv = defaultdict(set)
for cid, s in s15.items():
    for t in s:
        inv[t].add(cid)

# (가) 직접 짝
pairs = []   # (j, id24, id15, shared)
for c24, A in s24.items():
    cand = set()
    for t in A:
        cand |= inv.get(t, set())
    for c15 in cand:
        B = s15[c15]
        shared = A & B
        j = len(shared) / len(A | B)
        if j >= THR:
            pairs.append((j, c24, c15, shared))
pairs.sort(reverse=True, key=lambda x: x[0])

def noise(shared):
    return shared <= STOP

valid = [p for p in pairs if not noise(p[3])]
print(f"{'='*66}\n(가) 직접 1915↔1924 묶음 짝 (자카드≥{THR})\n{'='*66}")
print(f"전체 짝 {len(pairs)} · 노이즈(서수/범용어만) {len(pairs)-len(valid)} · 유효 {len(valid)}")
band = {"0.10~0.149":0,"0.15~0.199":0,"0.20+":0}
for j,_,_,_ in valid:
    band["0.20+" if j>=0.2 else "0.15~0.199" if j>=0.15 else "0.10~0.149"] += 1
print("유효 짝 유사도 구간:", band)

print(f"\n상위 12 유효 짝 (j · 1924묶음 · 1915묶음 · 공유토큰):")
for j,c24,c15,sh in valid[:12]:
    print(f"  {j:.3f}  {c24:18} {c15:18} {{{', '.join(list(sh)[:8])}}}")

# 착지: 1924 묶음의 장(C)/절·항
def parse(cid):  # C01-S01-I01-N01 -> ('C01','S01','I01')
    m = re.match(r"(C\d+)-(S\d+)-(I\d+)", cid)
    return m.groups() if m else (cid, "?", "?")

ch_cnt = defaultdict(int); ci_cnt = defaultdict(int)
for j,c24,c15,sh in valid:
    C,S,I = parse(c24)
    ch_cnt[C] += 1; ci_cnt[(C,S,I)] += 1
print(f"\n착지 장(1924) 분포 (유효 짝 {len(valid)}):")
for C,n in sorted(ch_cnt.items(), key=lambda x:-x[1]):
    print(f"  {C}: {n}  ({100*n/len(valid):.0f}%)")

topC = max(ch_cnt, key=ch_cnt.get)
print(f"\n최다 착지 장 {topC} 내 절-항 분포:")
for (C,S,I),n in sorted(ci_cnt.items(), key=lambda x:-x[1]):
    if C==topC and n>0:
        print(f"  {C}-{S}-{I}: {n}")

# (나) 哲學 소거
print(f"\n{'='*66}\n(나) 哲學 기표 묶음-단위\n{'='*66}")
print(f"哲學/철학 토큰 출현: 1915 = {m15.get('哲學',0)+m15.get('철학',0)}회 · "
      f"1924 = {m24.get('哲學',0)+m24.get('철학',0)}회")
# 역상관: topC 내 (S,I)별 참조밀도 vs 哲學 카운트
phil_by_si = defaultdict(int)
for cid, s in s24.items():
    C,S,I = parse(cid)
    if C==topC:
        # 哲學 멀티셋 카운트는 토큰파일 재집계 필요 → set 기준 출현 여부+묶음수로 근사
        pass
# 哲學 멀티셋을 (C,S,I)별로 재집계
phil_si = defaultdict(int); ref_si = defaultdict(int)
with open(NORM/"tokens_1924.csv", encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        if r["n_chunk_id"] and r["token"] in PHIL:
            C,S,I = parse(r["n_chunk_id"])
            phil_si[(C,S,I)] += 1
for (C,S,I),n in ci_cnt.items():
    ref_si[(C,S,I)] = n
print(f"\n{topC} 내 항별 [참조밀도 ↔ 哲學 빈도] (역상관 점검):")
keys = sorted(set(list(ci_cnt.keys())+[k for k in phil_si if k[0]==topC]),
              key=lambda k:-ref_si.get(k,0))
for k in keys:
    if k[0]==topC and (ref_si.get(k,0) or phil_si.get(k,0)):
        print(f"  {k[1]}-{k[2]}:  참조 {ref_si.get(k,0):2}  ·  哲學 {phil_si.get(k,0)}")
