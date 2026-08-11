# -*- coding: utf-8 -*-
"""분포 그림 패널 B의 '상위 꼬리'만 확대 — 직접·매개 도달 자카드 상위 150위.

전체 분포(make_dist_fig.py 패널 B)에서 매개 우위가 일어나는 왼쪽 끝(상위 ~5%)을
절대 순위(Top-K와 같은 축)로 확대해, 직접 천장과 매개의 초과를 또렷이 본다.
출력: appendix/매개분포_꼬리확대.svg / .png
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

NORM = Path(r"C:\hp_data\0_tnt\hyeonsang\_ocr_experiments\unified_db_2026-05-19\output\norm")
OUT = Path(__file__).parent.parent / "appendix"
_E = frozenset()
N = 150   # 상위 몇 위까지 확대


def load_bundles(fname):
    bc = defaultdict(set)
    with open(NORM / fname, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r["n_chunk_id"] and r["token"]:
                bc[r["n_chunk_id"]].add(r["token"])
    return [s for s in bc.values() if s]


def arrival(src, tgt):
    inv = defaultdict(set)
    for i, s in enumerate(tgt):
        for t in s:
            inv[t].add(i)
    out = []
    for s in src:
        cand = set()
        for t in s:
            cand |= inv.get(t, _E)
        bj = 0.0
        for i in cand:
            j = len(s & tgt[i]) / len(s | tgt[i])
            if j > bj:
                bj = j
        out.append(bj)
    return out


b1924 = load_bundles("tokens_1924.csv")
direct = sorted(arrival(load_bundles("tokens_1915.csv"), b1924), reverse=True)
medi = sorted(arrival(load_bundles("tokens_개벽.csv") + load_bundles("tokens_월보_win.csv"),
                      b1924), reverse=True)
ceil_d = direct[0]
print(f"직접 max={ceil_d:.4f} · 매개 max={medi[0]:.4f}")
for k in (10, 50, 100):
    print(f"  K={k}: 직접 {st.mean(direct[:k]):.4f} 매개 {st.mean(medi[:k]):.4f} "
          f"비율 {st.mean(medi[:k])/st.mean(direct[:k]):.2f}x")

fig, ax = plt.subplots(figsize=(8.6, 5.4))
xr = range(1, N + 1)
ax.fill_between(xr, direct[:N], medi[:N], color="#fde0db", zorder=1,
                label="매개 우위 폭")
ax.plot(xr, medi[:N], color="#c0392b", lw=2.2, zorder=3,
        label=f"매개 (잡지→1924)")
ax.plot(xr, direct[:N], color="#6c8ebf", lw=2.2, zorder=3,
        label=f"직접 (1915→1924)")
ax.axhline(ceil_d, ls=":", lw=1.3, color="#456", zorder=2)
ax.text(N, ceil_d, f"직접 천장 {ceil_d:.3f}  ", va="bottom", ha="right",
        fontsize=9.5, color="#456")

# Top-K 지점 표시
for k in (10, 50, 100):
    ax.axvline(k, ls="--", lw=0.9, color="#aaa", zorder=1)
    dm, mm = st.mean(direct[:k]), st.mean(medi[:k])
    ax.annotate(f"K={k}\n{mm/dm:.2f}×", (k, medi[0] * 0.96), fontsize=8.6,
                ha="center", va="top", color="#555")

ax.set_xlim(1, N)
ax.set_ylim(0, medi[0] * 1.04)
ax.set_xlabel("상위 순위 (묶음, 절대 순위 = Top-K 축)", fontsize=10.5)
ax.set_ylabel("1924 도달 자카드 (묶음별 최대)", fontsize=10.5)
ax.set_title("상위 꼬리 확대 — 직접 천장 위로 솟는 매개 상위 묶음 (상위 150위)",
             fontsize=12.5, fontweight="bold", pad=12)
ax.legend(loc="upper right", fontsize=9.5, frameon=True, framealpha=0.95)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)

fig.tight_layout()
fig.savefig(OUT / "매개분포_꼬리확대.svg", bbox_inches="tight")
fig.savefig(OUT / "매개분포_꼬리확대.png", dpi=190, bbox_inches="tight")
print(f"saved {OUT / '매개분포_꼬리확대.png'} / .svg")
