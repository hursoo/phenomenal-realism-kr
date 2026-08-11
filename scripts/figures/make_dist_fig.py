# -*- coding: utf-8 -*-
"""부록 분포 근거 그림 (2패널) — 두 층위 모두 매개도 F1(1915·1924 양끝 조화평균).

패널 A (위, 문장 묶음 단위): 잡지 묶음별 매개도 F1 분포(순위순). 소수 묶음만 높고 나머지는 낮다.
패널 B (아래, 글 단위): 글별 대표 매개도(top-5-mean F1) 순위 — 평균+2SD 위로 다섯 편만(클러스터).
출력: appendix/매개분포_그림.svg / .png
"""
import csv
import statistics as st
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

BASE = Path(r"C:\hp_data\0_tnt\hyeonsang\_ocr_experiments\unified_db_2026-05-19")
NORM = BASE / "output" / "norm"
CSV = BASE / "output" / "jaccard_topk5_wbwin_2026-05-24.csv"
OUT = Path(__file__).parent.parent / "appendix"
_E = frozenset()


def load_bundles(fname):
    bc = defaultdict(set)
    with open(NORM / fname, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r["n_chunk_id"] and r["token"]:
                bc[r["n_chunk_id"]].add(r["token"])
    return [s for s in bc.values() if s]


def inv_of(T):
    inv = defaultdict(set)
    for i, s in enumerate(T):
        for t in s:
            inv[t].add(i)
    return inv


def arrival(s, T, inv):
    cand = set()
    for t in s:
        cand |= inv.get(t, _E)
    bj = 0.0
    for i in cand:
        j = len(s & T[i]) / len(s | T[i])
        if j > bj:
            bj = j
    return bj


# ── 패널 A 데이터: 잡지 묶음별 매개도 F1 (양끝 조화평균) ──
b1915, b1924 = load_bundles("tokens_1915.csv"), load_bundles("tokens_1924.csv")
mag_b = load_bundles("tokens_개벽.csv") + load_bundles("tokens_월보_win.csv")
i15, i24 = inv_of(b1915), inv_of(b1924)
f1s = []
for s in mag_b:
    a15, a24 = arrival(s, b1915, i15), arrival(s, b1924, i24)
    f1s.append(2 * a15 * a24 / (a15 + a24) if (a15 + a24) > 0 else 0.0)
f1s.sort(reverse=True)
print(f"잡지 묶음 {len(f1s)} · 매개도 F1 max={f1s[0]:.4f} 중앙값={st.median(f1s):.4f}")

# ── 패널 B 데이터: 글별 대표 매개도(top-5-mean F1) ──
mags = []
with open(CSV, encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        if r["src"] in ("개벽", "월보") and r["f1_top5"]:
            mags.append((r["src"], r["c"], float(r["f1_top5"])))
mags.sort(key=lambda x: -x[2])
fvals = [m[2] for m in mags]
mu, sd = st.mean(fvals), st.stdev(fvals)
thr = mu + 2 * sd

# ── 그림 ──
fig, (axT, axB) = plt.subplots(2, 1, figsize=(8.8, 9.6))

# 위 패널 A: 묶음 매개도 F1 분포 (순위순, 수수하게)
axT.plot(range(1, len(f1s) + 1), f1s, color="#c0392b", lw=2.0)
axT.text(len(f1s) * 0.5, st.median(f1s) + 0.012,
         f"대다수 묶음은 낮다 (중앙값 {st.median(f1s):.3f})", fontsize=9, color="#666")
axT.text(len(f1s) * 0.18, f1s[0] * 0.78, "소수 묶음만 높다", fontsize=9.5, color="#a33")
axT.set_xlim(1, len(f1s))
axT.set_ylim(0, f1s[0] * 1.06)
axT.set_xlabel("매개도 순위 (잡지 문장 묶음, 높은 순)", fontsize=10)
axT.set_ylabel("매개도 F1 (1915·1924 양끝 조화평균)", fontsize=10)
axT.set_title("A. (문장 묶음 단위) 잡지 묶음별 매개도 분포",
              fontsize=10.8, fontweight="bold", loc="left")
for s in ("top", "right"):
    axT.spines[s].set_visible(False)

# 아래 패널 B: 글별 대표 매개도 클러스터
axB.scatter(range(1, len(mags) + 1), fvals, s=18, color="#b8c0cc", zorder=2)
axB.axhline(thr, ls="--", lw=1.4, color="#c0392b", zorder=1)
axB.text(58, thr, f"평균 +2 SD (z = +2) = {thr:.3f}", va="bottom", ha="right",
         fontsize=9.5, color="#c0392b")
COL = {"C53": "#d69e2e", "C72": "#0d9488"}
for i, (src, c, v) in enumerate(mags, 1):
    if v > thr:
        col = COL.get(c, "#2b6cb0")
        axB.scatter(i, v, s=64, color=col, edgecolors="white", linewidths=1.0, zorder=4)
        axB.annotate(f"{'월보 ' if src=='월보' else ''}{c}", (i, v), xytext=(i + 4, v),
                     fontsize=9, fontweight="bold", va="center", color=col, zorder=5)
    elif i == 6:
        axB.scatter(i, v, s=40, facecolors="none", edgecolors="#888", linewidths=1.0, zorder=3)
        axB.annotate(f"{c} (6위, 인접)", (i, v), xytext=(i + 4, v - 0.004), fontsize=8.3,
                     va="center", color="#666", zorder=3)
axB.set_xlim(-3, 60)
axB.set_ylim(0, max(fvals) * 1.12)
axB.set_xlabel("매개도 순위 (잡지 글 160편 중 상위 구간)", fontsize=10)
axB.set_ylabel("매개도 (글별 top-5-mean F1)", fontsize=10)
axB.set_title("B. (글 단위) 매개 클러스터: 다섯 편만 솟는다 (약 3%)",
              fontsize=10.8, fontweight="bold", loc="left")
for s in ("top", "right"):
    axB.spines[s].set_visible(False)

fig.tight_layout(h_pad=2.4)
fig.savefig(OUT / "매개분포_그림.svg", bbox_inches="tight")
fig.savefig(OUT / "매개분포_그림.png", dpi=190, bbox_inches="tight")
print(f"saved {OUT / '매개분포_그림.png'} / .svg")
