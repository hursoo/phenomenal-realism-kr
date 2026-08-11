# -*- coding: utf-8 -*-
"""Q4-1 분석의 도해 — 세 꼭지·세 변 역삼각형. analysis_checkpoints.md용."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

fig, ax = plt.subplots(figsize=(5.8, 4.1), dpi=150)
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

# 꼭지 좌표
B15 = (0.16, 0.80)   # 이노우에 1915 (좌상)
B24 = (0.84, 0.80)   # 이돈화 1924 (우상)
J   = (0.50, 0.16)   # 잡지 글 (하)

edge = dict(color="#333333", lw=2.0, zorder=1)
# 세 변
ax.plot([B15[0], B24[0]], [B15[1], B24[1]], **edge)              # 변① 직접
ax.plot([J[0], B15[0]],   [J[1], B15[1]],   **edge)              # 변② 매개 j15
ax.plot([J[0], B24[0]],   [J[1], B24[1]],   **edge)              # 변③ 매개 j24

NW, NH = 0.215, 0.115   # 세 꼭지 박스 동일 크기
def node(xy, label, fc):
    box = FancyBboxPatch((xy[0]-NW/2, xy[1]-NH/2), NW, NH,
                         boxstyle="round,pad=0.006,rounding_size=0.02",
                         fc=fc, ec="#222222", lw=1.3, zorder=3)
    ax.add_patch(box)
    ax.text(xy[0], xy[1], label, ha="center", va="center",
            fontsize=10.5, linespacing=1.45, zorder=4)

node(B15, "B_1915\n이노우에", "#dbe7f3")
node(B24, "B_1924\n이돈화",   "#dbe7f3")
node(J,   "J_wb, J_gb\n잡지 글 107편", "#f3ead9")

# 변① 라벨 — 변②·③과 동일하게 한 객체 두 줄(밀착)
ax.text(0.50, 0.865, "변①  직접(d)\n1915 ↔ 1924", ha="center", va="center",
        fontsize=10, color="#b03030", fontweight="bold")

# 2·3변 라벨 — 수평
ax.text(0.195, 0.478, "변②  매개(j15)\n잡지 ↔ 1915", ha="center", va="center",
        fontsize=10, color="#0a6e0a", fontweight="bold")
ax.text(0.805, 0.478, "변③  매개(j24)\n잡지 ↔ 1924", ha="center", va="center",
        fontsize=10, color="#0a6e0a", fontweight="bold")

fig.tight_layout()
fig.savefig("분석삼각형.png", bbox_inches="tight", facecolor="white")
fig.savefig("분석삼각형.svg", bbox_inches="tight", facecolor="white")
print("saved 분석삼각형.png / .svg")
