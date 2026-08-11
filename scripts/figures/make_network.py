# -*- coding: utf-8 -*-
"""
인내천요의 매개 경로 네트워크 도판 생성.

스케치(raw/network_idea.jpg)를 충실히 재현:
  - x축 = 발행 시점, 두 스윔레인(개벽 위 / 천도교회월보 아래)
  - 좌하 『철학과 종교』(1915) 박스 → 클러스터 글 (변②, 굵기 ∝ 1915 친화 edge2_top5)
  - 클러스터 글 → 우상 『인내천요의』(1924) 박스 (변③, 굵기 ∝ 1924 친화 edge3_top5)
  - 글 점: 전체 160편 옅은 배경 + 클러스터 5글 강조(크기 ∝ f1_top5)
  - C53은 매개 아닌 '동시산출 자매' → 점선으로 구분

데이터: _ocr_experiments/unified_db_2026-05-19/output/jaccard_topk5_2026-05-22.csv
출력  : figures/network.svg, figures/network.png
"""
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

CSV = Path(r"C:\hp_data\0_workspaces\0_tnt\hyeonsang\_ocr_experiments"
           r"\unified_db_2026-05-19\output\jaccard_topk5_2026-05-22.csv")
OUT = Path(__file__).parent

# 클러스터 5글의 발행일 보정(CSV 결측분은 draft 본문 호수→발행월 기준)
DATE_FIX = {"C19": "1921-01-01", "C22": "1921-02-01", "C23": "1921-02-01"}
# 표시 라벨(개벽 호수·약칭)
LABEL = {
    "C53": "C53 「世界三大宗敎…人乃天主義」\n(개벽45호, 1924-03)",
    "C22": "C22 「科學上으로 본 生老病死」\n(백두산인, 개벽8호, 1921-02)",
    "C43": "C43 「吾人의 新死生觀」\n(개벽20호, 1922-02)",
    "C19": "C19 「意識上으로 觀한 自我의 觀念」\n(인내천연구 其七, 1921-01)",
    "C23": "C23 「疑問者에게 答함」\n(인내천연구 其八, 1921-02)",
}
CLUSTER = ["C53", "C22", "C43", "C19", "C23"]


def to_year(d):
    if not d:
        return None
    y, m, *rest = d.split("-")
    day = rest[0] if rest else "15"
    return int(y) + (int(m) - 1) / 12 + (int(day) - 1) / 365.0


def load():
    arts = {"개벽": [], "월보": []}
    cluster = {}
    with open(CSV, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r["src"] not in ("개벽", "월보"):
                continue
            c = r["c"]
            date = DATE_FIX.get(c, r["date"]) if c in CLUSTER else r["date"]
            rec = {
                "c": c, "src": r["src"], "year": to_year(date),
                "e2": float(r["edge2_top5"] or 0),
                "e3": float(r["edge3_top5"] or 0),
                "f1": float(r["f1_top5"] or 0),
            }
            arts[r["src"]].append(rec)
            # C-번호는 매체 간 중복(개벽·월보 각각 C19 등) → 클러스터는 개벽만
            if c in CLUSTER and r["src"] == "개벽":
                cluster[c] = rec
    return arts, cluster


def main():
    arts, cluster = load()

    LANE = {"개벽": 2.25, "월보": 1.25}          # 스윔레인 y
    BOOK15 = (1914.6, -0.15)                      # 『철학과 종교』 좌하
    BOOK24 = (1924.9, 3.35)                       # 『인내천요의』 우상
    XMIN, XMAX = 1914.0, 1925.6

    fig, ax = plt.subplots(figsize=(13, 7.2))

    # ── 스윔레인 배경 띠 ──
    for src, y in LANE.items():
        ax.axhspan(y - 0.42, y + 0.42, xmin=(1919.3 - XMIN) / (XMAX - XMIN),
                   xmax=(1925.0 - XMIN) / (XMAX - XMIN),
                   color="#eef2f7", zorder=0)
        ax.text(1919.45, y + 0.33, f"『{ '개벽(開闢)' if src=='개벽' else '천도교회월보' }』",
                fontsize=11, color="#4a5568", va="top", ha="left", style="italic")

    # ── 배경 점: 전체 160편(클러스터 제외) ──
    for src, y in LANE.items():
        for rec in arts[src]:
            # 개벽 클러스터 5글만 배경에서 제외(월보 동명 글은 배경 유지)
            if (src == "개벽" and rec["c"] in CLUSTER) or rec["year"] is None:
                continue
            ax.scatter(rec["year"], y, s=14, color="#b8c2cc",
                       edgecolors="none", alpha=0.55, zorder=2)

    # ── 두 단행본 박스 ──
    def book_box(xy, w, h, title, sub, face):
        x, y = xy
        ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                     boxstyle="round,pad=0.02,rounding_size=0.08",
                     fc=face, ec="#2d3748", lw=1.6, zorder=5))
        ax.text(x, y + 0.10, title, ha="center", va="center",
                fontsize=12, fontweight="bold", zorder=6)
        ax.text(x, y - 0.22, sub, ha="center", va="center",
                fontsize=8.5, color="#4a5568", zorder=6)

    book_box(BOOK15, 1.7, 0.95,
             "이노우에 데쓰지로\n『哲學と宗敎』(1915)",
             "C02 실재론 · C08 메치니코프\n· C13/C14 종교비교", "#fde8e8")
    book_box(BOOK24, 1.8, 0.95,
             "이돈화\n『人乃天要義』(1924)",
             "C03 인내천 哲理(I04·I05·I06)\n· C06 雜感", "#e6f4ea")

    # ── 클러스터 점 + 라벨 ──
    # 1921년에 C19·C22·C23이 몰려 있어 점은 미세 x-지터, 라벨은 지시선으로 분산
    JIT = {"C19": -0.18, "C22": 0.0, "C23": 0.18}
    # 라벨 위치(절대 좌표)와 정렬
    LABEL_AT = {
        "C53": (1923.0, 3.05, "center"),
        "C43": (1922.2, 2.95, "center"),
        "C19": (1916.7, 2.95, "center"),
        "C22": (1917.1, 1.05, "center"),
        "C23": (1920.4, 0.55, "center"),
    }
    cl_pos = {}
    for c in CLUSTER:
        rec = cluster[c]
        y = LANE[rec["src"]]
        x = rec["year"] + JIT.get(c, 0.0)
        cl_pos[c] = (x, y)
        is_sib = (c == "C53")
        ax.scatter(x, y, s=140 + rec["f1"] * 1400,
                   color=("#d69e2e" if is_sib else "#2b6cb0"),
                   edgecolors="white", linewidths=1.4, zorder=6)
        lx, ly, ha = LABEL_AT[c]
        ax.annotate(LABEL[c], (x, y), xytext=(lx, ly),
                    ha=ha, va="center", fontsize=8.2,
                    color="#1a202c", zorder=7,
                    arrowprops=dict(arrowstyle="-", color="#a0aec0", lw=0.8),
                    bbox=dict(boxstyle="round,pad=0.3", fc="white",
                              ec=("#d69e2e" if is_sib else "#90cdf4"), lw=1.0))

    # ── 변② 화살표: 1915 책 → 클러스터 글 (굵기 ∝ e2) ──
    for c in CLUSTER:
        rec, (x, y) = cluster[c], cl_pos[c]
        ax.add_patch(FancyArrowPatch(
            BOOK15, (x, y - 0.16),
            connectionstyle="arc3,rad=0.18",
            arrowstyle="-|>", mutation_scale=12,
            lw=0.8 + rec["e2"] * 9, color="#e53e3e", alpha=0.55, zorder=3))

    # ── 변③ 화살표: 클러스터 글 → 1924 책 (굵기 ∝ e3) ──
    for c in CLUSTER:
        rec, (x, y) = cluster[c], cl_pos[c]
        sib = (c == "C53")
        ax.add_patch(FancyArrowPatch(
            (x, y + 0.16), BOOK24,
            connectionstyle="arc3,rad=-0.12",
            arrowstyle="-|>", mutation_scale=13,
            lw=0.8 + rec["e3"] * 9,
            color=("#d69e2e" if sib else "#2b6cb0"),
            linestyle=("--" if sib else "-"),
            alpha=0.75, zorder=4))

    # ── 레인 내 곡선 화살표: 클러스터 형성 흐름(1921→1922) ──
    ax.add_patch(FancyArrowPatch(
        cl_pos["C19"], cl_pos["C43"],
        connectionstyle="arc3,rad=-0.45",
        arrowstyle="-|>", mutation_scale=11,
        lw=1.4, color="#718096", alpha=0.6, zorder=3))

    # ── 연도축 ──
    for yr in (1915, 1920, 1924):
        ax.axvline(yr, color="#cbd5e0", lw=0.8, ls=":", zorder=0)
    ax.set_xlim(XMIN, XMAX)
    ax.set_ylim(-0.9, 4.1)
    ax.set_xticks([1915, 1920, 1924])
    ax.set_xticklabels(["1915", "1920", "1924"], fontsize=11)
    ax.set_yticks([])
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#a0aec0")
    ax.set_title("이노우에 『철학과 종교』(1915) → 매개 클러스터(개벽) → 『인내천요의』(1924)\n"
                 "매개 경로의 어휘 친화 네트워크",
                 fontsize=13.5, fontweight="bold", pad=14)

    # ── 범례 ──
    from matplotlib.lines import Line2D
    leg = [
        Line2D([0], [0], color="#e53e3e", lw=2.5, alpha=0.6,
               label="변② 1915→글 친화(굵기 ∝ edge2)"),
        Line2D([0], [0], color="#2b6cb0", lw=2.5,
               label="변③ 글→1924 친화(굵기 ∝ edge3)"),
        Line2D([0], [0], color="#d69e2e", lw=2.5, ls="--",
               label="C53 동시산출 자매(매개 아님)"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#b8c2cc",
               markersize=7, label="잡지 글 160편(배경)"),
    ]
    ax.legend(handles=leg, loc="lower right", fontsize=8.6,
              frameon=True, framealpha=0.95)

    fig.tight_layout()
    fig.savefig(OUT / "network.svg", bbox_inches="tight")
    fig.savefig(OUT / "network.png", dpi=200, bbox_inches="tight")
    print("saved:", OUT / "network.svg", "+ network.png")


if __name__ == "__main__":
    main()
