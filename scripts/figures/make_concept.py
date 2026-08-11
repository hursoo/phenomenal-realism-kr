# -*- coding: utf-8 -*-
"""§2 간이 개념 흐름도 (본문용) — 약어·통계 없이 논리 흐름만.

상세 순서도(appendix/인내천논증_순서도)와 짝을 이루는 *간이판*. 본문 §2 초입에서
독자가 분석의 큰 그림(사료→직접 vs 매개→두 갈래→회수→번안)을 한눈에 잡도록.
V1/V2/V3·j15/j24·top-5-mean·Top-K·z·δ 같은 장치는 일부러 뺐다(그것은 상세 순서도·본문).

출력: appendix/인내천논증_개념도.svg / .png
"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False
HERE = Path(__file__).parent
OUT = HERE.parent / "appendix"

fig, ax = plt.subplots(figsize=(8.6, 9.4))
ax.set_xlim(-4.6, 4.6)
ax.set_ylim(-1.1, 9.0)
ax.axis("off")


def box(x, y, w, h, title, body, fc, ec, tfs=11.5, bfs=9.8):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                 boxstyle="round,pad=0.02,rounding_size=0.10",
                 fc=fc, ec=ec, lw=1.5, zorder=3))
    if body:
        ax.text(x, y + h * 0.24, title, ha="center", va="center",
                fontsize=tfs, fontweight="bold", color="#1a202c", zorder=4)
        ax.text(x, y - h * 0.22, body, ha="center", va="center",
                fontsize=bfs, color="#2d3748", zorder=4, linespacing=1.5)
    else:
        ax.text(x, y, title, ha="center", va="center",
                fontsize=tfs, fontweight="bold", color="#1a202c", zorder=4)


def arrow(p, q, rad=0.0):
    ax.add_patch(FancyArrowPatch(p, q, connectionstyle=f"arc3,rad={rad}",
                 arrowstyle="-|>", mutation_scale=15, lw=1.6,
                 color="#4a5568", zorder=2, shrinkA=3, shrinkB=3))


# ── 구역 배경 ──
ax.add_patch(FancyBboxPatch((-4.45, 1.15), 8.9, 5.35,
             boxstyle="round,pad=0.02,rounding_size=0.06",
             fc="#f4f4f6", ec="#d0d0d8", lw=1.0, zorder=0))
ax.text(-4.30, 6.35, "2.1  경로의 발견", ha="left", va="top",
        fontsize=12.5, fontweight="bold", color="#374151", zorder=1)
ax.add_patch(FancyBboxPatch((-2.95, -0.55), 5.9, 1.25,
             boxstyle="round,pad=0.02,rounding_size=0.06",
             fc="#f4f4f6", ec="#d0d0d8", lw=1.0, zorder=0))
ax.text(-2.78, 0.05, "2.2", ha="left", va="center",
        fontsize=12.5, fontweight="bold", color="#374151", zorder=1)

# ── 노드 ──
box(0, 7.7, 7.6, 1.15, "자료와 가공",
    "이노우에 1915 · 이돈화 잡지(개벽·월보) · 이돈화 1924\n→ 정규화 · 문장 묶음(자료 간 단위 통일)",
    "#fde9d9", "#c0504d")
box(0, 5.75, 5.8, 1.05, "양 끝점 매개도 측정",
    "1915·1924 양쪽 모두 닮은 정도 = 매개도\n(직접 전수는 따로 점검: 천장 0.22)",
    "#ece8f6", "#7a6cae")
box(-2.35, 3.75, 3.5, 1.35, "갈래 A · 경로 점검",
    "직접 전수는 막히고\n매개는 소수에 집중\n→ 집중된 굴절", "#dae8fc", "#6c8ebf")
box(2.4, 3.75, 3.7, 1.35, "갈래 B · 주요 매개 글",
    "양 끝을 잇는 매개 클러스터\n개벽 C53·C22·C43·C19\n+ 월보 C72", "#e2efda", "#82a878")
box(0, 1.85, 5.0, 0.95, "경로 = 집중된 굴절 → 회수",
    "(어휘 친화 네트워크 그림)", "#e1d5e7", "#9673a6", tfs=11.5, bfs=9.2)
box(0, 0.05, 4.2, 0.9, "번안 양상", "소거 ⊂ 회수", "#dbe5f1", "#4f81bd")

# ── 화살표 ──
arrow((0, 7.12), (0, 6.28))
arrow((-1.4, 5.25), (-2.1, 4.45), rad=0.12)
arrow((1.5, 5.25), (2.15, 4.45), rad=-0.12)
arrow((-2.1, 3.07), (-0.9, 2.30), rad=-0.12)
arrow((2.15, 3.07), (0.95, 2.30), rad=0.12)
arrow((0, 1.37), (0, 0.52))

ax.set_title("그림 — §2 분석의 흐름 (개념도)", fontsize=14, fontweight="bold", pad=14)
fig.tight_layout()
fig.savefig(OUT / "인내천논증_개념도.svg", bbox_inches="tight")
fig.savefig(OUT / "인내천논증_개념도.png", dpi=190, bbox_inches="tight")
print(f"saved {OUT / '인내천논증_개념도.png'} / .svg")
