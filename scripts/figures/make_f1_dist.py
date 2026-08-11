# -*- coding: utf-8 -*-
"""매개도(F1) 분포 — 잡지 묶음 2,783개. 4-3 (다) 2단용. (묶음 단위, 글/클러스터 라벨 없음)
   본문이 든 수치(중앙 0.058·0.1↑·0.15↑·최대 0.267·floor 545)를 그래프에 표시."""
import sys, csv, statistics as st
from collections import defaultdict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

NORM = r"C:\hp_data\0_tnt\hyeonsang\_ocr_experiments\unified_db_2026-05-19\output\norm"
def load(src):
    bc = defaultdict(set)
    with open(f"{NORM}\\tokens_{src}.csv", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r["n_chunk_id"] and r["token"]:
                bc[r["n_chunk_id"]].add(r["token"])
    return {k: v for k, v in bc.items() if v}
B = {s: load(s) for s in ("1915","1924","개벽","월보_win")}
# 개벽은 ≤1924-03(C01~C53)만 — 책 이후 글(C54~) 제외
B["개벽"] = {k:v for k,v in B["개벽"].items() if int(k.split("-")[0][1:])<=53}
# (A) 대칭 시간창: 월보도 발간(1915-02-12) 이후만 — pre-1915 32편 제외
import json as _json, pandas as _pd
_wb = _pd.read_excel(r"C:\hp_data\0_tnt\hyeonsang\_ocr_experiments\unified_db_2026-05-19\output\MA_YD_10-20_WB.xlsx")
_wb["c"]=_wb["n_chunk_id"].map(lambda x:str(x).split("-")[0])
_wb["pub"]=_wb["src_metadata"].map(lambda s:_json.loads(s).get("publish_date") if isinstance(s,str) else None)
_post=set(_wb.groupby("c")["pub"].first().map(lambda d:_pd.Timestamp(d)).pipe(lambda x:x[x>=_pd.Timestamp("1915-02-12")].index))
B["월보_win"] = {k:v for k,v in B["월보_win"].items() if k.split("-")[0] in _post}
def inv(bd):
    arr=list(bd.values()); ix=defaultdict(set)
    for i,s in enumerate(arr):
        for t in s: ix[t].add(i)
    return arr,ix
A15,I15=inv(B["1915"]); A24,I24=inv(B["1924"])
def jflo(a,b):
    sh=len(a&b); return sh/len(a|b) if sh>=2 else 0.0
def best(s,arr,ix):
    c=set()
    for t in s: c|=ix.get(t,set())
    return max((jflo(s,arr[i]) for i in c), default=0.0)
def harm(a,b): return 0.0 if a+b==0 else 2*a*b/(a+b)
F1=[]
for src in ("개벽","월보_win"):
    for s in B[src].values():
        F1.append(harm(best(s,A15,I15), best(s,A24,I24)))
F1.sort(reverse=True)
n=len(F1); med=st.median(F1); mx=F1[0]
n0=sum(1 for x in F1 if x==0); n10=sum(1 for x in F1 if x>=0.10); n15=sum(1 for x in F1 if x>=0.15)
print(f"n={n} median={med:.4f} max={mx:.4f} | 0={n0} >=.10={n10} >=.15={n15}")

GRY="#8a8a8a"; RED="#e8000d"; BLU="#34495e"
fig,(axL,axR)=plt.subplots(1,2,figsize=(10.2,4.1),dpi=150)

# ── 좌: 내림차순 순위 곡선 + 기준선 ──
axL.plot(range(1,n+1), F1, color="#4f81a8", lw=1.4, zorder=3)
for y,lab,col in [(0.15,f"0.15 ↑ {n15}개",GRY),(0.10,f"0.10 ↑ {n10}개 ({n10/n*100:.0f}%)",GRY),(med,f"중앙값 {med:.3f}",RED)]:
    axL.axhline(y, color=col, ls="--", lw=1.5 if col==RED else 1.0, zorder=2)
    axL.text(n*0.99, y+0.004, lab, color=col, ha="right", va="bottom", fontsize=9, fontweight="bold")
axL.annotate(f"최댓값 {mx:.3f}", xy=(1,mx), xytext=(n*0.16,mx-0.012),
             fontsize=9.5, color=BLU, fontweight="bold",
             arrowprops=dict(arrowstyle="->", color=BLU))
# floor 끝 절벽
rank0=n-n0+1
axL.annotate(f"끝 {n0}개 = 0 (floor)", xy=(rank0, 0.0), xytext=(n*0.42, 0.035),
             fontsize=9, color=BLU, arrowprops=dict(arrowstyle="->", color=BLU))
axL.set_xlabel("잡지 묶음 순위 (매개도 높은 순)", fontsize=10)
axL.set_ylabel("매개도 F1", fontsize=10)
axL.set_title(f"① 매개도 내림차순 ({n:,} 묶음)", fontsize=11)
axL.set_ylim(0, mx*1.10); axL.spines[["top","right"]].set_visible(False)

# ── 우: 히스토그램 (로그 y) + 기준선 ──
axR.hist(F1, bins=46, range=(0,mx), color="#4f81a8", ec="#2f5876", lw=0.4, zorder=3)
top=axR.get_ylim()[1]
axR.axvline(med, color=RED, ls="--", lw=1.8, zorder=4)
axR.text(med, top*0.88, f"중앙값 {med:.3f}  ", color=RED, ha="right", va="center", fontsize=9, fontweight="bold")
for x,lab in [(0.10,f"0.10↑ {n10}개({n10/n*100:.0f}%)"),(0.15,f"0.15↑ {n15}개")]:
    axR.axvline(x, color=GRY, ls=":", lw=1.2, zorder=4)
    axR.text(x, top*0.5, " "+lab, color=GRY, ha="left", va="center", fontsize=8.5, fontweight="bold", rotation=90)
axR.annotate(f"floor {n0}개 (=0)", xy=(0.004, top*0.97), xytext=(0.035, top*0.82),
             fontsize=8.5, color=BLU, arrowprops=dict(arrowstyle="->", color=BLU))
axR.set_xlabel("매개도 F1", fontsize=10)
axR.set_ylabel("묶음 수", fontsize=10)
axR.set_title("② 매개도 히스토그램 (선형 눈금 — 막대 면적 = 비중)", fontsize=11)
axR.spines[["top","right"]].set_visible(False)

fig.tight_layout()
fig.savefig("매개도분포.png", bbox_inches="tight", facecolor="white")
fig.savefig("매개도분포.svg", bbox_inches="tight", facecolor="white")
print("saved 매개도분포.png / .svg")
