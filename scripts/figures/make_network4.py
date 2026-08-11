# -*- coding: utf-8 -*-
"""4축 어휘 친화 네트워크 (관계 유형별 top-N 선별, 4컬럼 층위 레이아웃).

축: 1915 『철학과 종교』 장 │ 천도교회월보 글 │ 개벽 글 │ 1924 『인내천요의』 장.
공정 선별: 모든 단위 쌍 top-5-mean 자카드(compute_unit_sim.py)를
  관계 유형(10종) 각각에서 top-N만 채택 — 한 축이 분포를 독식하지 않게.
  inter(축 사이) top INTER_N, intra(축 내부 연속성) top INTRA_N, 각 sim 바닥 적용.
레이아웃: 4컬럼(시간순). 책=장 노드 수직 적재, 잡지=발행일 순 적재.
인코딩: 엣지 굵기 ∝ sim, 색=관계 유형 / 방향=시간. intra는 컬럼 옆 곡선 호.

입력 : figures/unit_sim.csv(compute_unit_sim.py — reading-space norm 토큰), figures/mag_meta.csv(잡지 제목·발행일; 토큰화 무관 메타)
출력 : figures/network4.svg / network4.png
"""
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
from matplotlib.lines import Line2D

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

HERE = Path(__file__).parent

# ── 선별 파라미터 ──
INTER_N, INTER_FLOOR = 6, 0.035    # 축 사이: 유형별 상위 6
# 연결선 시간 컷오프: 인내천요의 초판 발행(1924-03) 이후 잡지 글은 매개일 수 없음 → 제외
CUTOFF = (1924, 3)

COLX = {"1915": 0.0, "개벽": 1.0, "1924": 2.0}
RANK = {"1915": 0, "개벽": 1, "1924": 2}

# 1915 『哲學と宗敎』 장 간략 제목(원 목차 기반)
CH1915 = {
    "C00": "C00 序", "C01": "C01 철학의 요구·장래", "C02": "C02 실재론(유물·유심)",
    "C03": "C03 진화론", "C04": "C04 의지·자아", "C05": "C05 사생 문제",
    "C06": "C06 생명의 5특징", "C07": "C07 생리학자 생명론", "C08": "C08 메치니코프 학설",
    "C09": "C09 오이켄 철학", "C10": "C10 동서철학 일치", "C11": "C11 동양철학 특색",
    "C12": "C12 불·기·신도", "C13": "C13 기독교와 유교", "C14": "C14 불교·기독교 차이",
    "C15": "C15 불교소감", "C16": "C16 자국종교 장래", "C17": "C17 자국종교 혁신",
    "C18": "C18 종교와 교육", "C19": "C19 死종교·活종교", "C20": "C20 선교50년 감상",
    "C21": "C21 아국종교 전도", "C22": "C22 일본종교 통일", "C23": "C23 금후 교육·종교",
    "C24": "C24 古종교·현대도덕", "C25": "C25 신도 과거·장래", "C26": "C26 일본신화 新해석",
    "C27": "C27 [부록]민족기원", "C28": "C28 [부록]인종론"}
# 1924 『人乃天要義』 장 간략 제목
CH1924 = {"C01": "C01 서언", "C02": "C02 인내천과 천도", "C03": "C03 인내천과 진리",
          "C04": "C04 인내천의 목적", "C05": "C05 인내천의 수련", "C06": "C06 인내천 雜感"}
CLUSTER = {"C53", "C22", "C43", "C19", "C23"}
# 원 제목 오타 교정(표시용; raw 불변). 월보 C40 觀ᄒᆞᆯ(할)은 觀한이 옳음.
TITLE_FIX = {("월보", "C40"): "信仰上으로 觀한 吾人의 努力"}

RT_COLOR = {"1915↔개벽": "#e53e3e", "1924↔개벽": "#2b6cb0", "1915↔1924": "#805ad5"}


def to_year(d):
    if not d:
        return 9999
    y, m, *_ = d.split("-")
    return int(y) + (int(m) - 1) / 12


def fix_oldhangul(t):
    """옛한글 아래아(ᆞ) 합성 자모 → 모던 음절(아래아→ㅏ). 예: ᄒᆞᆯ→할, ᄒᆞᆫ→한, ᄒᆞ→하.
    Malgun Gothic이 conjoining jamo(U+1100~)를 렌더링 못해 □로 깨지는 것을 해소."""
    out, i = [], 0
    while i < len(t):
        ch = t[i]
        if 0x1100 <= ord(ch) <= 0x1112 and i + 1 < len(t) and ord(t[i + 1]) == 0x119E:
            L = ord(ch) - 0x1100          # 초성
            T, adv = 0, 2                 # 종성 없음
            if i + 2 < len(t) and 0x11A8 <= ord(t[i + 2]) <= 0x11C2:
                T, adv = ord(t[i + 2]) - 0x11A7, 3
            out.append(chr(0xAC00 + (L * 21 + 0) * 28 + T))   # 중성 0 = ㅏ
            i += adv
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def brief(title, n=13):
    """기사 제목 간략화: 부제(— …)·괄호·쉼표/등호 이후 절단 후 길이 제한."""
    import re
    t = (title or "").replace("教", "敎")   # 教→敎 (Malgun에 教 없음)
    t = fix_oldhangul(t)                     # 옛한글 아래아 합성 → 모던 음절
    t = re.split(r"\s*[—–]", t)[0]          # 부제(엠대시) 제거
    t = re.sub(r"\([^)]*\)", "", t)          # 괄호 제거
    t = re.split(r"[,=]", t)[0]              # 쉼표·등호 이후 제거
    t = t.strip()
    return (t[:n] + "…") if len(t) > n else t


def after_cutoff(meta, node):
    """잡지 노드가 CUTOFF(1924-03) 이후면 True. 책·날짜불명은 False(유지)."""
    if node[0] not in ("개벽", "월보"):
        return False
    d = meta.get(node, ("", ""))[0]
    if not d:
        return False
    y, m, *_ = d.split("-")
    return (int(y), int(m)) > CUTOFF


def load_meta():
    """잡지 (src,c) -> (date, title). mag_meta.csv(src_metadata 추출, 결측 보간)를 권위로 사용."""
    meta = {}
    with open(HERE / "mag_meta.csv", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            meta[(r["src"], r["c"])] = (r["date"], r["title"])
    return meta


def select_edges(meta):
    # 3축(1915·개벽·1924)의 *축 간(inter)* 관계만. 월보 축·모든 축내부(intra) 제거.
    by_rt = defaultdict(list)
    with open(HERE / "unit_sim.csv", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r["kind"] == "intra":
                continue                       # 동일 축 간 관계 제거
            a = (r["axisA"], r["unitA"])
            b = (r["axisB"], r["unitB"])
            if "월보" in (a[0], b[0]):
                continue                       # 월보 축 제거
            if after_cutoff(meta, a) or after_cutoff(meta, b):
                continue                       # 1924-03 이후 잡지 글 제외
            by_rt[r["reltype"]].append(
                dict(a=a, b=b, sim=float(r["sim"]), rt=r["reltype"], kind="inter"))
    kept = []
    for rt, es in by_rt.items():
        es.sort(key=lambda e: e["sim"], reverse=True)
        kept += [e for e in es[:INTER_N] if e["sim"] >= INTER_FLOOR]

    # 본문 서술 취지 반영(매개 경로 중심 + 종교비교 동시 접속):
    #  · 1915→1924 직접 엣지는 제거(수치상 인공물). 단 종교비교→雜感(1924 C06)만 존치.
    #  · 개벽 C53(「세계3대종교」)은 동시산출 자매 — 철학과종교가 C53과 C06에 *각각 직접*
    #    연결(동시 접속). 따라서 1915→C53(자원 유입)은 살리고, C53→1924(매개로 보이는) 엣지만 제외.
    def keep(e):
        if e["rt"] == "1915↔1924":
            u24 = e["a"][1] if e["a"][0] == "1924" else e["b"][1]
            return u24 == "C06"
        if ("개벽", "C53") in (e["a"], e["b"]):
            return e["rt"] == "1915↔개벽"      # 1915→C53만 존치, C53→1924 제외
        return True
    return [e for e in kept if keep(e)]


def main():
    meta = load_meta()
    edges = select_edges(meta)
    nodes = set()
    for e in edges:
        nodes.add(e["a"]); nodes.add(e["b"])
    print(f"채택 엣지 {len(edges)} · 노드 {len(nodes)}")
    # 관계 유형별 개수(3축 inter만)
    from collections import Counter as _C
    cnt = _C(e["rt"] for e in edges)
    print("  유형별 개수(inter):")
    for rt in ["1915↔개벽", "1924↔개벽", "1915↔1924"]:
        print(f"    {rt:12} {cnt.get(rt, 0)}")

    # ── 노드 좌표 ──
    # 잡지(개벽·월보): 각 컬럼 안에서 연월 순으로 균등 배치(이른 글=위). 연도 라벨 부기.
    # 단행본(1915·1924): 목차(장번호) 순으로 균등 적재.
    Y_TOP, Y_BOT = 4.0, -4.0
    col_nodes = defaultdict(list)
    for n in nodes:
        col_nodes[n[0]].append(n)
    pos = {}
    node_year = {}      # 잡지 노드 -> 연(라벨용)
    for axn, ns in col_nodes.items():
        if axn in ("개벽", "월보"):
            # 연월 순, 동일 호수는 C-번호 순(예: C22 위·C23 아래)
            ns.sort(key=lambda n: (to_year(meta.get(n, ("", ""))[0]), n[1]))
        else:
            ns.sort(key=lambda n: n[1])                                # 목차 순
        k = len(ns)
        gap = (Y_TOP - Y_BOT) / max(k - 1, 1)
        for i, n in enumerate(ns):
            pos[n] = (COLX[axn], Y_TOP - i * gap)      # i=0(첫 장·이른 글)이 맨 위
            if axn in ("개벽", "월보"):
                node_year[n] = (meta.get(n, ("", ""))[0] or "")[:7]

    fig, ax = plt.subplots(figsize=(12, 8.6))

    # 컬럼 헤더
    HEAD = {"1915": "이노우에\n『哲學と宗敎』(1915-02)\n— 장(목차순)",
            "개벽": "이돈화\n: 개벽 글(연월순)",
            "1924": "이돈화\n『人乃天要義』(1924-03)\n— 장(목차순)"}
    ytop = Y_TOP + 1.1
    for axn, x in COLX.items():
        ax.text(x, ytop, HEAD[axn], ha="center", va="bottom",
                fontsize=10.5, fontweight="bold", color="#1a202c")
        ax.axvline(x, color="#e2e8f0", lw=0.8, zorder=0)
    # 개벽 컬럼 = 매개. 회수 박스와 짝을 이루는 둥근 사각형 라벨
    ax.text(COLX["개벽"], Y_TOP + 0.55, "매개", ha="center", va="center",
            fontsize=11, fontweight="bold", color="#b45309", zorder=9,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#dd6b20", lw=1.2))

    # ── inter 엣지(축 사이): 시간 방향 화살표 ──
    for e in edges:
        a, b = e["a"], e["b"]
        src, dst = (a, b) if RANK[a[0]] <= RANK[b[0]] else (b, a)
        (xa, ya), (xb, yb) = pos[src], pos[dst]
        span = RANK[dst[0]] - RANK[src[0]]
        rad = 0.04 + 0.05 * (span - 1)        # 컬럼 건너뛰면 더 휨
        col = RT_COLOR.get(e["rt"], "#999")
        ax.add_patch(FancyArrowPatch((xa, ya), (xb, yb),
                     connectionstyle=f"arc3,rad={rad}",
                     arrowstyle="-|>", mutation_scale=12,
                     lw=0.8 + e["sim"] * 7.5, color=col, alpha=0.7,
                     zorder=(5 if e["sim"] > 0.2 else 3),
                     shrinkA=8, shrinkB=8))

    # ── 노드 + 라벨 ──
    for n in nodes:
        x, y = pos[n]
        axn, c = n
        is_book = axn in ("1915", "1924")
        is_cl = (axn == "개벽" and c in CLUSTER)
        if is_book:
            fc = "#fde8e8" if axn == "1915" else "#e6f4ea"
            ax.scatter(x, y, s=210, marker="s", color=fc,
                       edgecolors="#2d3748", linewidths=1.2, zorder=6)
            txt = CH1915.get(c, c) if axn == "1915" else CH1924.get(c, c)
            ha = "right" if axn == "1915" else "left"
            dx = -0.14 if axn == "1915" else 0.14
            ax.annotate(txt, (x, y), xytext=(x + dx, y), ha=ha, va="center",
                        fontsize=8.6, color="#1a202c", zorder=7)
        elif is_cl:
            ax.scatter(x, y, s=110, color=("#d69e2e" if c == "C53" else "#2b6cb0"),
                       edgecolors="white", linewidths=1.2, zorder=6)
            tt = brief(TITLE_FIX.get(n) or meta.get(n, ("", ""))[1])
            yr = node_year.get(n, "")
            ax.annotate(f"{tt} ({c}, {yr})", (x, y), xytext=(x + 0.11, y), ha="left",
                        va="center", fontsize=8.6, fontweight="bold", zorder=8,
                        color=("#9c6a13" if c == "C53" else "#1d4ed8"))
        else:
            ax.scatter(x, y, s=62, color="#a9b4c0", edgecolors="white",
                       linewidths=0.8, zorder=4)
            tt = brief(TITLE_FIX.get(n) or meta.get(n, ("", ""))[1])
            yr = node_year.get(n, "")
            ax.annotate(f"{tt} ({c}, {yr})", (x, y), xytext=(x + 0.11, y), ha="left",
                        va="center", fontsize=8.6, color="#475569", zorder=5)

    # ── 회수(回收) 라벨: 변③ 파란 화살표가 인내천哲理(C03)로 수렴하는 지점(노드 수직 아래) ──
    if ("1924", "C03") in pos:
        cx, cy = pos[("1924", "C03")]
        ax.text(cx, cy - 0.55, "회수", ha="center", va="center",
                fontsize=11, fontweight="bold", color="#1d4ed8", zorder=9,
                bbox=dict(boxstyle="round,pad=0.3", fc="white",
                          ec="#2b6cb0", lw=1.2))

    ax.set_xlim(-0.9, 2.9)
    ax.set_ylim(min(y for _, y in pos.values()) - 0.9, ytop + 1.4)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ("top", "right", "left", "bottom"):
        ax.spines[s].set_visible(False)
    ax.set_title("어휘 친화 분포로 본 매개와 회수", fontsize=14, fontweight="bold", pad=16)

    leg = [
        Line2D([0], [0], color="#e53e3e", lw=2.6, label="1915→개벽 (변②, 자원 유입)"),
        Line2D([0], [0], color="#2b6cb0", lw=2.6, label="개벽→1924 (변③, 회수 도달)"),
        Line2D([0], [0], color="#805ad5", lw=2.6, label="1915 → 1924 (변①, 직접·동시 흡수)"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#2b6cb0",
               markersize=9, label="매개 클러스터 글"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#d69e2e",
               markersize=9, label="'잡감'과 동시산출"),
    ]
    ax.legend(handles=leg, loc="upper left", bbox_to_anchor=(0.0, 0.05),
              fontsize=8.6, frameon=True, framealpha=0.95)

    fig.tight_layout()
    fig.savefig(HERE / "network4.svg", bbox_inches="tight")
    fig.savefig(HERE / "network4.png", dpi=190, bbox_inches="tight")
    print("saved network4.svg / network4.png")


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    main()
