# -*- coding: utf-8 -*-
"""매개 구조 2D 산점도 — 잡지 묶음을 (1915 닮음 × 1924 닮음) 평면에.

진짜 매개 = 양끝 모두 높은 오른쪽 위. C53(동시산출) = 1924만 높은 왼쪽 위.
이노우에 베낌 = 1915만 높은 오른쪽 아래. 직접 천장(1915↔1924 최대 0.22)을 참조 격자로.
출력: appendix/매개2D_그림.svg / .png  (시험용 — 채택 시 매개분포_그림 대체 검토)
"""
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mp

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

NORM = Path(r"C:\hp_data\0_tnt\hyeonsang\_ocr_experiments\unified_db_2026-05-19\output\norm")
OUT = Path(__file__).parent.parent / "appendix"
CLUSTER = {("개벽", "C53"), ("개벽", "C22"), ("개벽", "C43"), ("개벽", "C19"), ("월보", "C72")}
DIRECT = 0.2188
_E = frozenset()


def load_meta(fname):
    bc, meta = {}, {}
    with open(NORM / fname, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            cid = r["n_chunk_id"]
            if cid and r["token"]:
                bc.setdefault(cid, set()).add(r["token"])
                meta[cid] = (r["src"], r["c"])
    return bc, meta


def tokens_only(fname):
    return [s for s in load_meta(fname)[0].values() if s]


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


t1915, t1924 = tokens_only("tokens_1915.csv"), tokens_only("tokens_1924.csv")
i15, i24 = inv_of(t1915), inv_of(t1924)
pts = []   # (src, c, a15, a24)
for fn in ("tokens_개벽.csv", "tokens_월보_win.csv"):
    bc, meta = load_meta(fn)
    for cid, s in bc.items():
        if not s:
            continue
        pts.append((meta[cid][0], meta[cid][1], arrival(s, t1915, i15), arrival(s, t1924, i24)))

# 직접 1915↔1924 비교(변①) 주변 분포용
direct_to_1924 = [arrival(s, t1924, i24) for s in t1915]   # 1915 묶음 → 1924 (직접, 세로축)
direct_to_1915 = [arrival(s, t1915, i15) for s in t1924]   # 1924 묶음 → 1915 (직접, 가로축)
mag_a15 = [a for _, _, a, _ in pts]
mag_a24 = [b for _, _, _, b in pts]

both = [(s, c, a, b) for s, c, a, b in pts if a > DIRECT and b > DIRECT]
print(f"잡지 묶음 {len(pts)} · 양끝 모두 0.22 초과 = {len(both)}개 {[(c, round(a,2), round(b,2)) for _,c,a,b in both]}")
print(f"직접 1915→1924 max={max(direct_to_1924):.3f} · 1924→1915 max={max(direct_to_1915):.3f}")

# 메인 + 두 주변 분포 레이아웃
fig = plt.figure(figsize=(9.8, 9.4))
gs = fig.add_gridspec(2, 2, width_ratios=(5, 1.1), height_ratios=(1.1, 5),
                      left=0.09, right=0.97, bottom=0.08, top=0.93, wspace=0.04, hspace=0.04)
ax = fig.add_subplot(gs[1, 0])
axtop = fig.add_subplot(gs[0, 0], sharex=ax)
axrt = fig.add_subplot(gs[1, 1], sharey=ax)
bins = [i * 0.02 for i in range(33)]
axtop.hist(direct_to_1915, bins=bins, density=True, color="#9aa0aa", alpha=0.55, label="직접 (1924↔1915)")
axtop.hist(mag_a15, bins=bins, density=True, histtype="step", color="#c0392b", lw=1.6, label="잡지 → 1915")
axtop.axvline(DIRECT, ls=":", lw=1.1, color="#888")
axtop.legend(fontsize=7.6, loc="upper right", frameon=False)
axtop.set_yticks([]); axtop.tick_params(labelbottom=False)
for sp in ("top", "right", "left"): axtop.spines[sp].set_visible(False)
axrt.hist(direct_to_1924, bins=bins, density=True, orientation="horizontal", color="#9aa0aa", alpha=0.55)
axrt.hist(mag_a24, bins=bins, density=True, orientation="horizontal", histtype="step", color="#c0392b", lw=1.6)
axrt.axhline(DIRECT, ls=":", lw=1.1, color="#888")
axrt.set_xticks([]); axrt.tick_params(labelleft=False)
for sp in ("top", "right", "bottom"): axrt.spines[sp].set_visible(False)
axtop.text(0.30, axtop.get_ylim()[1] * 0.5, "회색=직접  빨강=잡지", fontsize=7.6, color="#666")
# 직접 천장 참조 격자 + 양끝 초과 구역
ax.axvspan(DIRECT, 1, ymin=DIRECT / 0.62, color="#eef4e3", zorder=0)
ax.axhline(DIRECT, ls=":", lw=1.3, color="#888", zorder=1)
ax.axvline(DIRECT, ls=":", lw=1.3, color="#888", zorder=1)
ax.text(0.005, DIRECT + 0.004, "1924 천장 0.22", fontsize=9, color="#777")
ax.text(DIRECT + 0.004, 0.004, "1915 천장 0.22", fontsize=9, color="#777", rotation=90, va="bottom")
ax.plot([0, 0.62], [0, 0.62], ls="--", lw=0.9, color="#ccc", zorder=1)  # y=x 균형선

ARTCOL = {"C53": "#d69e2e", "C22": "#2b6cb0", "C43": "#c0392b", "C19": "#6f9e57", "C72": "#0d9488"}
for src, c, a, b in pts:
    if (src, c) not in CLUSTER:
        ax.scatter(a, b, s=8, color="#c8cdd6", alpha=0.30, zorder=2, linewidths=0)
for src, c, a, b in pts:
    if (src, c) in CLUSTER:
        ax.scatter(a, b, s=40, color=ARTCOL.get(c, "#2b6cb0"), edgecolors="white",
                   linewidths=0.6, alpha=0.92, zorder=4)
# 유일한 '양끝 다리' 묶음 강조
for s, c, a, b in both:
    ax.scatter(a, b, s=150, facecolors="none", edgecolors="#2f6e1f", linewidths=1.8, zorder=6)
    ax.annotate(f"양끝 모두 0.22↑\n묶음은 단 1개 ({c})", (a, b), xytext=(a - 0.12, b + 0.09),
                fontsize=9.5, color="#2f6e1f", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color="#2f6e1f", lw=1.1))

# 구역 주석 (큰 글씨)
ax.text(0.10, 0.55, "↑ 1924만 높음\n동시산출 (C53)", fontsize=11, color="#a06a00", va="top", fontweight="bold")
ax.text(0.46, 0.045, "1915만 높음 → 이노우에 베낌 (C22) →", fontsize=11, color="#1f4e79",
        ha="center", fontweight="bold")
ax.text(0.07, 0.07, "대다수: 양끝 다 낮음", fontsize=9.5, color="#888")

handles = [mp.Patch(color=ARTCOL[c], label=("월보 " if ("월보", c) in CLUSTER else "") + c)
           for c in ("C53", "C22", "C43", "C19", "C72")]
handles.append(mp.Patch(color="#c8cdd6", label="클러스터 밖"))
ax.legend(handles=handles, loc="upper right", fontsize=9.5, ncol=1, frameon=True, framealpha=0.97)

ax.set_xlim(0, 0.62)
ax.set_ylim(0, 0.62)
ax.set_xlabel("1915 닮음  (이노우에 『철학과 종교』 도달 유사도)", fontsize=11)
ax.set_ylabel("1924 닮음  (이돈화 『인내천요의』 도달 유사도)", fontsize=11)
fig.suptitle("잡지 묶음의 매개 구조 — '양끝 다리'가 아니라 출처(1915)·표적(1924) 쪽으로 갈린다\n(가장자리: 직접 1915↔1924 분포는 회색, 잡지는 빨강)",
             fontsize=12, fontweight="bold", x=0.09, ha="left")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
fig.savefig(OUT / "매개2D_그림.svg", bbox_inches="tight")
fig.savefig(OUT / "매개2D_그림.png", dpi=190, bbox_inches="tight")
print(f"saved {OUT / '매개2D_그림.png'} / .svg")
