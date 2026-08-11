# -*- coding: utf-8 -*-
"""4축 어휘 친화 네트워크 (관계 유형별 top-N 선별, 4컬럼 층위 레이아웃).

축: 1915 『철학과 종교』 장 │ 천도교회월보 글 │ 개벽 글 │ 1924 『인내천요의』 장.
공정 선별: 모든 단위 쌍 top-5-mean 자카드(compute_unit_sim.py)를
  관계 유형(10종) 각각에서 top-N만 채택 — 한 축이 분포를 독식하지 않게.
  inter(축 사이) top INTER_N, intra(축 내부 연속성) top INTRA_N, 각 sim 바닥 적용.
레이아웃: 4컬럼(시간순). 책=장 노드 수직 적재, 잡지=발행일 순 적재.
인코딩: 엣지 굵기 ∝ sim, 색=관계 유형 / 방향=시간. intra는 컬럼 옆 곡선 호.

[백업] 4축(월보 포함) + 축 내부(intra) 연속성 보존 버전. 메인은 make_network4.py(3축).
입력 : figures/unit_sim.csv, mag_meta.csv
출력 : figures/network4_4axis.svg / network4_4axis.png
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
INTRA_N, INTRA_FLOOR = 4, 0.08     # 축 내부: 유형별 상위 4
# 연결선 시간 컷오프: 인내천요의 초판 발행(1924-03) 이후 잡지 글은 매개일 수 없음 → 제외
CUTOFF = (1924, 3)

COLX = {"1915": 0.0, "월보": 1.0, "개벽": 2.0, "1924": 3.0}
RANK = {"1915": 0, "월보": 1, "개벽": 2, "1924": 3}

# 1915 『哲學と宗敎』 장 간략 제목(원 목차 기반)
CH1915 = {
    "C00": "C00 序", "C01": "C01 철학의 요구·장래", "C02": "C02 실재론(유물·유심)",
    "C03": "C03 진화론", "C04": "C04 의지·자아", "C05": "C05 사생 문제",
    "C06": "C06 생명의 5특징", "C07": "C07 생리학자 생명론", "C08": "C08 메치니코프 학설",
    "C09": "C09 오이켄 철학", "C10": "C10 동서철학 일치", "C11": "C11 동양철학 특색",
    "C12": "C12 불·기·신도", "C13": "C13 기독교와 유교", "C14": "C14 불교·기독교 차이",
    "C15": "C15 불교소감", "C16": "C16 자국종교 장래", "C17": "C17 자국종교 혁신",
    "C18": "C18 종교와 교육", "C19": "C19 死종교·活종교", "C20": "C20 선교50년 감상",
    "C21": "C21 자국종교 전도", "C22": "C22 일본종교 통일", "C23": "C23 금후 교육·종교",
    "C24": "C24 古종교·현대도덕", "C25": "C25 신도 과거·장래", "C26": "C26 일본신화 新해석",
    "C27": "C27 [부록]민족기원", "C28": "C28 [부록]인종론"}
# 1924 『人乃天要義』 장 간략 제목
CH1924 = {"C01": "C01 서언", "C02": "C02 인내천과 천도", "C03": "C03 인내천과 진리",
          "C04": "C04 인내천의 목적", "C05": "C05 인내천의 수련", "C06": "C06 인내천 雜感"}
CLUSTER = {"C53", "C22", "C43", "C19", "C23"}
# 원 제목 오타 교정(표시용; raw 불변). 월보 C40 觀ᄒᆞᆯ(할)은 觀한이 옳음.
TITLE_FIX = {("월보", "C40"): "信仰上으로 觀한 吾人의 努力"}

RT_COLOR = {"1915↔개벽": "#e53e3e", "1924↔개벽": "#2b6cb0", "1915↔1924": "#805ad5",
            "개벽↔월보": "#dd6b20", "1915↔월보": "#e53e3e", "1924↔월보": "#2b6cb0"}
INTRA_COLOR = "#94a3b8"


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
    # 4축 전체 + 축 내부(intra) 포함. 관계 유형별 top-N(inter top6·intra top4).
    by_rt = defaultdict(list)
    with open(HERE / "unit_sim.csv", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            a = (r["axisA"], r["unitA"])
            b = (r["axisB"], r["unitB"])
            if after_cutoff(meta, a) or after_cutoff(meta, b):
                continue                       # 1924-03 이후 잡지 글 제외
            by_rt[r["reltype"]].append(
                dict(a=a, b=b, sim=float(r["sim"]), rt=r["reltype"], kind=r["kind"]))
    kept = []
    for rt, es in by_rt.items():
        es.sort(key=lambda e: e["sim"], reverse=True)
        if es[0]["kind"] == "intra":
            n, fl = INTRA_N, INTRA_FLOOR
        else:
            n, fl = INTER_N, INTER_FLOOR
        kept += [e for e in es[:n] if e["sim"] >= fl]

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
    # 관계 유형별 개수(축 간 6 + 축 내부 4)
    from collections import Counter as _C
    cnt = _C(e["rt"] for e in edges)
    print("  유형별 개수:")
    for rt in ["1915↔개벽", "1915↔월보", "1915↔1924", "개벽↔월보", "1924↔개벽",
               "1924↔월보", "1915↔1915", "개벽↔개벽", "월보↔월보", "1924↔1924"]:
        kind = "intra" if rt.split("↔")[0] == rt.split("↔")[1] else "inter"
        print(f"    [{kind}] {rt:12} {cnt.get(rt, 0)}")

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
            ns.sort(key=lambda n: to_year(meta.get(n, ("", ""))[0]))   # 연월 순
        else:
            ns.sort(key=lambda n: n[1])                                # 목차 순
        k = len(ns)
        gap = (Y_TOP - Y_BOT) / max(k - 1, 1)
        for i, n in enumerate(ns):
            pos[n] = (COLX[axn], Y_TOP - i * gap)      # i=0(첫 장·이른 글)이 맨 위
            if axn in ("개벽", "월보"):
                node_year[n] = (meta.get(n, ("", ""))[0] or "")[:7]

    fig, ax = plt.subplots(figsize=(15.5, 9))

    # 컬럼 헤더
    HEAD = {"1915": "이노우에\n『哲學と宗敎』(1915-02)\n— 장(목차순)",
            "월보": "『천도교회월보』\n글(연월순)", "개벽": "『개벽』\n글(연월순)",
            "1924": "이돈화\n『人乃天要義』(1924-03)\n— 장(목차순)"}
    ytop = Y_TOP + 1.1
    for axn, x in COLX.items():
        ax.text(x, ytop, HEAD[axn], ha="center", va="bottom",
                fontsize=10.5, fontweight="bold", color="#1a202c")
        ax.axvline(x, color="#e2e8f0", lw=0.8, zorder=0)
    # 월보 주석: 측정 한계
    ax.text(COLX["월보"], min(y for _, y in pos.values()) - 0.7,
            "※ 월보는 단행본과 같은 척도로 비교 불가\n(글 짧음·청크 밀도 높음 — length_corrected 참조)",
            ha="center", va="top", fontsize=7.6, color="#c05621", style="italic")

    # ── intra 엣지(축 내부 연속성): 곡선 호 ──
    for e in edges:
        if e["kind"] != "intra":
            continue
        (xa, ya), (xb, yb) = pos[e["a"]], pos[e["b"]]
        rad = 0.6 if ya != yb else 0.3
        ax.add_patch(FancyArrowPatch((xa, ya), (xb, yb),
                     connectionstyle=f"arc3,rad={rad}",
                     arrowstyle="-", mutation_scale=1,
                     lw=0.8 + e["sim"] * 7, color=INTRA_COLOR,
                     alpha=0.55, zorder=2, linestyle=(0, (3, 2))))

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
                        fontsize=7.6, color="#1a202c", zorder=7)
        elif is_cl:
            ax.scatter(x, y, s=110, color=("#d69e2e" if c == "C53" else "#2b6cb0"),
                       edgecolors="white", linewidths=1.2, zorder=6)
            tt = brief(TITLE_FIX.get(n) or meta.get(n, ("", ""))[1])
            yr = node_year.get(n, "")
            ax.annotate(f"{tt} ({yr})", (x, y), xytext=(x + 0.11, y), ha="left",
                        va="center", fontsize=7.2, fontweight="bold", zorder=8,
                        color=("#9c6a13" if c == "C53" else "#1d4ed8"))
        else:
            ax.scatter(x, y, s=62, color="#a9b4c0", edgecolors="white",
                       linewidths=0.8, zorder=4)
            tt = brief(TITLE_FIX.get(n) or meta.get(n, ("", ""))[1])
            yr = node_year.get(n, "")
            ax.annotate(f"{tt} ({yr})", (x, y), xytext=(x + 0.11, y), ha="left",
                        va="center", fontsize=6.4, color="#475569", zorder=5)

    ax.set_xlim(-0.9, 3.9)
    ax.set_ylim(min(y for _, y in pos.values()) - 1.2, ytop + 1.4)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ("top", "right", "left", "bottom"):
        ax.spines[s].set_visible(False)
    ax.set_title("[백업·4축] 어휘 친화 네트워크 — 『哲學と宗敎』(1915-02) │ 천도교회월보 │ 개벽 │ 『人乃天要義』(1924-03)\n"
                 f"유형별 top{INTER_N}(inter)·top{INTRA_N}(intra) · 1915→1924 직접 제외(종교비교→雜感 예외) · 1924-03 컷오프",
                 fontsize=11, fontweight="bold", pad=14)

    leg = [
        Line2D([0], [0], color="#e53e3e", lw=2.6, label="1915→개벽/월보 (변②, 자원 유입)"),
        Line2D([0], [0], color="#2b6cb0", lw=2.6, label="개벽/월보→1924 (변③, 회수 도달)"),
        Line2D([0], [0], color="#805ad5", lw=2.6, label="종교비교→雜感 직접 (1915 C13/C14→1924 C06)"),
        Line2D([0], [0], color="#dd6b20", lw=2.6, label="개벽↔월보 (잡지 간)"),
        Line2D([0], [0], color=INTRA_COLOR, lw=2.0, ls=(0, (3, 2)), label="축 내부 연속성 (intra)"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#2b6cb0",
               markersize=9, label="매개 클러스터 글"),
    ]
    ax.legend(handles=leg, loc="upper left", bbox_to_anchor=(0.0, 0.05),
              fontsize=8.2, frameon=True, framealpha=0.95)

    fig.tight_layout()
    fig.savefig(HERE / "network4_4axis.svg", bbox_inches="tight")
    fig.savefig(HERE / "network4_4axis.png", dpi=190, bbox_inches="tight")
    print("saved network4_4axis.svg / network4_4axis.png")


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    main()
