# -*- coding: utf-8 -*-
"""그림 3 — 글 단위 매개도(top-5-mean) 분포 107편(개벽 53 + 월보 54, 1915-02~1924-03 대칭창) + z>+2 경계·매개 클러스터. 4-3 (라)용."""
import sys, csv, statistics as st
from collections import defaultdict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False
NORM = r"C:\hp_data\0_tnt\hyeonsang\_ocr_experiments\unified_db_2026-05-19\output\norm"
def load_c(src):
    bc={}; cof={}
    with open(f"{NORM}\\tokens_{src}.csv", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r["n_chunk_id"] and r["token"]:
                bc.setdefault(r["n_chunk_id"],set()).add(r["token"]); cof[r["n_chunk_id"]]=r["c"]
    return {k:v for k,v in bc.items() if v}, cof
def load(src):
    bc=defaultdict(set)
    with open(f"{NORM}\\tokens_{src}.csv", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r["n_chunk_id"] and r["token"]: bc[r["n_chunk_id"]].add(r["token"])
    return {k:v for k,v in bc.items() if v}
B15,B24=load("1915"),load("1924")
# (A) 대칭 시간창: 월보 발간(1915-02-12) 이후만 — pre-1915 32편 제외
import json as _json, pandas as _pd
_wb=_pd.read_excel(r"C:\hp_data\0_tnt\hyeonsang\_ocr_experiments\unified_db_2026-05-19\output\MA_YD_10-20_WB.xlsx")
_wb["c"]=_wb["n_chunk_id"].map(lambda x:str(x).split("-")[0])
_wb["pub"]=_wb["src_metadata"].map(lambda s:_json.loads(s).get("publish_date") if isinstance(s,str) else None)
WB_POST=set(_wb.groupby("c")["pub"].first().map(lambda d:_pd.Timestamp(d)).pipe(lambda x:x[x>=_pd.Timestamp("1915-02-12")].index))
def inv(bd):
    a=list(bd.values()); ix=defaultdict(set)
    for i,s in enumerate(a):
        for t in s: ix[t].add(i)
    return a,ix
A15,I15=inv(B15); A24,I24=inv(B24)
def jf(a,b):
    sh=len(a&b); return sh/len(a|b) if sh>=2 else 0.0
def best(s,a,ix):
    c=set()
    for t in s: c|=ix.get(t,set())
    return max((jf(s,a[i]) for i in c),default=0.0)
def h(a,b): return 0 if a+b==0 else 2*a*b/(a+b)
by=defaultdict(list)
for src in("개벽","월보_win"):
    bd,cof=load_c(src)
    for cid,s in bd.items():
        if src=="개벽" and int(cof[cid][1:])>53: continue  # 책 이후(C54~) 제외
        if src=="월보_win" and cof[cid] not in WB_POST: continue  # (A) 월보 pre-1915 제외
        by[(src,cof[cid])].append(h(best(s,A15,I15),best(s,A24,I24)))
def t5(v): v=sorted(v,reverse=True); return sum(v[:5])/min(5,len(v))
glow={g:t5(v) for g,v in by.items()}
items=sorted(glow.items(), key=lambda x:-x[1])
vals=[v for _,v in items]
mu=st.mean(vals); sd=st.pstdev(vals); z2=mu+2*sd
print(f"n={len(vals)} mean={mu:.4f} sd={sd:.4f} z2={z2:.4f}")
LAB={("개벽","C53"):"C53","개벽C22":"C22"}
def lab(g):
    src,c=g; return f"{c}(월보)" if src=="월보_win" else c
top6=items[:6]

fig,ax=plt.subplots(figsize=(8.4,4.6),dpi=150)
x=range(1,len(vals)+1)
ax.scatter(x, vals, s=14, color="#9bb7cf", ec="none", zorder=3)
# 상위 6 강조 (지시선으로 라벨 분산)
labpos={1:(7,0.224),2:(7,0.171),3:(17,0.156),4:(31,0.147),5:(47,0.137),6:(62,0.124)}
for i,(g,v) in enumerate(top6,1):
    cl = "#e8000d" if v>=z2 else "#e69500"
    ax.scatter([i],[v], s=46, color=cl, ec="#222", lw=0.5, zorder=5)
    tx,ty=labpos[i]
    ax.annotate(lab(g), (i,v), xytext=(tx,ty), fontsize=9, fontweight="bold", color=cl,
                arrowprops=dict(arrowstyle="-", color=cl, lw=0.7, shrinkA=0, shrinkB=3))
ax.axhline(mu, color="#888", ls="--", lw=1.1)
ax.text(len(vals)*0.99, mu+0.003, f"평균 {mu:.3f}", color="#888", ha="right", va="bottom", fontsize=9)
ax.axhline(z2, color="#e8000d", ls="--", lw=1.6)
ax.text(len(vals)*0.99, z2+0.004, f"z = +2 경계 ({z2:.3f}) — 위로 솟은 4편 = 확정 클러스터",
        color="#e8000d", ha="right", va="bottom", fontsize=9, fontweight="bold")
ax.set_xlabel(f"글 순위 (매개도 top-5-mean 높은 순, {len(vals)}편)", fontsize=10)
ax.set_ylabel("글 매개도 (top-5-mean)", fontsize=10)
ax.set_title("글 단위 매개도 분포와 매개 클러스터 (개벽 53 + 월보 54, 1915-02~1924-03 대칭창)", fontsize=11)
ax.set_ylim(0, vals[0]*1.12); ax.spines[["top","right"]].set_visible(False)
fig.tight_layout()
fig.savefig("매개클러스터.png", bbox_inches="tight", facecolor="white")
fig.savefig("매개클러스터.svg", bbox_inches="tight", facecolor="white")
print("saved 매개클러스터.png / .svg")
