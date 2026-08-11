# -*- coding: utf-8 -*-
"""변① 직접 비교(928,560 묶음쌍) 자카드 분포 — analysis_checkpoints.md (다)용."""
import csv
from collections import defaultdict
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

NORM = Path(r"C:\hp_data\0_tnt\hyeonsang\_ocr_experiments\unified_db_2026-05-19\output\norm")
def load(src):
    bc = defaultdict(set)
    with open(NORM / f"tokens_{src}.csv", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r["n_chunk_id"] and r["token"]:
                bc[r["n_chunk_id"]].add(r["token"])
    return [s for s in bc.values() if s]

b15, b24 = load("1915"), load("1924")
n0 = n1 = n2 = 0
nonzero = []
for s in b15:
    for t in b24:
        sh = len(s & t)
        if sh == 0:
            n0 += 1
            continue
        j = sh / len(s | t)
        nonzero.append(j)
        if sh == 1:
            n1 += 1
        else:
            n2 += 1
import statistics as st
N = len(b15) * len(b24)
mx = max(nonzero)
med = st.median(nonzero)
print(f"N={N:,} 0개={n0:,}({n0/N*100:.1f}%) 1개={n1:,}({n1/N*100:.1f}%) "
      f"2+={n2:,}({n2/N*100:.1f}%) median={med:.4f} max={mx:.4f}")

fig, (axL, axR) = plt.subplots(1, 2, figsize=(9.2, 3.9), dpi=150)

# ── 좌: 공유 개념어 개수별 묶음쌍 비율 ──
cats = ["공유 0개", "공유 1개", "공유 2개+"]
pcts = [n0 / N * 100, n1 / N * 100, n2 / N * 100]
colors = ["#c0504d", "#e8b04b", "#4f81a8"]
bars = axL.bar(cats, pcts, color=colors, ec="#333", lw=0.8, width=0.62)
for b, p in zip(bars, pcts):
    axL.text(b.get_x() + b.get_width() / 2, p + 1.5, f"{p:.1f}%",
             ha="center", va="bottom", fontsize=11, fontweight="bold")
axL.set_ylim(0, 95)
axL.set_ylabel("묶음쌍 비율 (%)", fontsize=10)
axL.set_title("① 공유 개념어 개수별 분포\n(928,560 묶음쌍)", fontsize=11)
axL.spines[["top", "right"]].set_visible(False)

# ── 우: 공유가 있는 짝의 자카드 분포 (로그 y) ──
axR.hist(nonzero, bins=44, range=(0, 0.22), color="#4f81a8", ec="#2f5876", lw=0.4)
axR.set_yscale("log")
axR.axvline(med, color="#e8000d", lw=2.4, ls="--")
axR.text(med, axR.get_ylim()[1] * 0.42, f"중간값 {med:.3f}  ",
         color="#e8000d", fontsize=11, ha="right", va="center", fontweight="bold")
axR.axvline(mx, color="#1565c0", lw=2.4, ls="--")
axR.text(mx, axR.get_ylim()[1] * 0.5, f"  최댓값(천장) {mx:.3f}",
         color="#1565c0", fontsize=9.5, ha="left", va="center", fontweight="bold")
axR.set_xlabel("자카드 유사도", fontsize=10)
axR.set_ylabel("짝 수 (로그)", fontsize=10)
axR.set_title("② 공유가 있는 짝의 자카드 분포\n(공유 1개+ = 16.5%, 로그 눈금)", fontsize=11)
axR.spines[["top", "right"]].set_visible(False)

fig.tight_layout()
fig.savefig("변1_자카드분포.png", bbox_inches="tight", facecolor="white")
fig.savefig("변1_자카드분포.svg", bbox_inches="tight", facecolor="white")
print("saved 변1_자카드분포.png / .svg")
