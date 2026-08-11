# -*- coding: utf-8 -*-
"""회수(回收) before/after 도해 (본문 §2.2용) — 한 절 안의 후퇴와 채움.

「靈魂과 人乃天」 항을 사례로, 도입부에 남은 외래 메타라벨이 종결부의 교단 어휘로
교체되는 곡선을 한눈에 보인다. 회수 = 후퇴(외래 표지, 陰) + 채움(교단 어휘, 陽).
수치·약어 없이 개념만(상세는 본문 §2.2·다섯 양상 표).

출력: appendix/회수_도식.svg / .png
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

fig, ax = plt.subplots(figsize=(9.2, 4.5))
ax.set_xlim(-5.2, 5.2)
ax.set_ylim(-1.7, 3.0)
ax.axis("off")


def box(x, y, w, h, title, body, fc, ec, tcol="#1a202c", bcol="#2d3748",
        tfs=11.5, bfs=10.2):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                 boxstyle="round,pad=0.02,rounding_size=0.10",
                 fc=fc, ec=ec, lw=1.6, zorder=3))
    ax.text(x, y + h * 0.30, title, ha="center", va="center",
            fontsize=tfs, fontweight="bold", color=tcol, zorder=4)
    ax.text(x, y - h * 0.18, body, ha="center", va="center",
            fontsize=bfs, color=bcol, zorder=4, linespacing=1.55)


# ── 두 단락: 도입부(후퇴) → 종결부(채움) ──
box(-3.05, 0.9, 3.7, 2.25, "도입부 단락",
    "외래 메타라벨 잔존\n\n唯物論者 · 近代科學\n物質論者",
    "#ededf0", "#9aa0aa", tcol="#4a5568", bcol="#6b7280")
box(3.05, 0.9, 3.7, 2.25, "종결부 단락",
    "교단 고유어로 정초\n\n人乃天 · 宇宙의 活精\n사람性 · 大神師",
    "#e2efda", "#6f9e57", tcol="#2f5e1f", bcol="#33691e")

# ── 회수 화살표 ──
ax.add_patch(FancyArrowPatch((-1.05, 0.9), (1.05, 0.9),
             arrowstyle="-|>", mutation_scale=26, lw=3.0,
             color="#9673a6", zorder=2, shrinkA=2, shrinkB=2))
ax.text(0, 1.62, "회수(回收)", ha="center", va="center",
        fontsize=13.5, fontweight="bold", color="#6b4a86", zorder=5)
ax.text(0, 0.28, "후퇴(陰)\n+\n채움(陽)", ha="center", va="center",
        fontsize=8.8, color="#6b4a86", zorder=5, linespacing=1.2)

# ── 한 절(「靈魂과 人乃天」)의 흐름임을 명시 ──
ax.text(0, 2.55, "한 절(「靈魂과 人乃天」 항) 안의 전개", ha="center", va="center",
        fontsize=10.5, color="#374151", style="italic")
ax.text(0, -1.25,
        "외래 표지가 물러난 자리(소거)에 교단 어휘가 들어서는 한 운동의 양면 — 소거 ⊂ 회수",
        ha="center", va="center", fontsize=10.2, color="#4a5568")

ax.set_title("그림 — 회수: 한 절 안에서 외래 표지가 교단 어휘로 교체되는 곡선",
             fontsize=13.5, fontweight="bold", pad=12)
fig.tight_layout()
fig.savefig(OUT / "회수_도식.svg", bbox_inches="tight")
fig.savefig(OUT / "회수_도식.png", dpi=190, bbox_inches="tight")
print(f"saved {OUT / '회수_도식.png'} / .svg")
