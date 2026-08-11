# -*- coding: utf-8 -*-
"""어휘 유사도 네트워크 v5 — 매개 클러스터에 월보 C72 편입 (2026-05-24 정본).

make_network4.py의 후속 버전. 변경점:
  · 월보를 28토큰 윈도우(tokens_월보_win.csv)로 본 unit_sim.csv를 입력.
  · 매개 클러스터 = 개벽 C53·C22·C43·C19 + **월보 C72**((A) 대칭 시간창에서 C72 z=+1.98로 경계지만 자연 단절(6/7) 위라 편입; 내용 매개 확증 — 4-3 라/라보).
  · 월보 축은 여전히 통째로는 제외하되, **C72 한 노드만** 매개(개벽) 컬럼에 들인다.
  · 변①(직접) = 종교비교→雜感(C06) + 實在·生命→哲理(C03). 哲理는 매개·직접 겹층(4-4).
입력 : figures/unit_sim.csv(compute_unit_sim.py, 월보=윈도우), figures/mag_meta.csv
출력 : appendix/매개회수그림.svg / .png   (인내천논증_순서도과 함께 appendix에서 관리)
       (구판 figures/network4.png은 그대로 보존)
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
WOLBO_N = 2                        # 월보 C72는 양쪽 각 상위 2엣지만(단일 노드 과밀 방지)
CUTOFF = (1924, 3)                 # 인내천요의 초판(1924-03) 이후 잡지 글은 매개 불가

COLX = {"1915": 0.0, "개벽": 1.0, "1924": 2.0}
RANK = {"1915": 0, "개벽": 1, "월보": 1, "1924": 2}   # 월보(C72)는 매개 컬럼(=개벽 자리)

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
CH1924 = {"C01": "C01 서언", "C02": "C02 인내천과 천도", "C03": "C03 인내천과 진리",
          "C04": "C04 인내천의 목적", "C05": "C05 인내천의 수련", "C06": "C06 인내천 雜感"}
CLUSTER = {"C53", "C22", "C43", "C19"}       # 개벽 매개 클러스터(C23 제외)
WOLBO_CL = ("월보", "C72")                    # 월보 측 매개 노드
TITLE_FIX = {("월보", "C40"): "信仰上으로 觀한 吾人의 努力"}
# 변①(직접) 채택 끝점 — top-N이 아니라 4-4 분석의 *개념 범주*로 명시 선별.
#   (u15, u24) 쌍. 種교비교 → 雜感(C06)은 동시 흡수(기존).
#   實在(C02 唯物·唯心·實在論)·生命(C06·C07 機械論↔活精論) → 哲理(C03)는 직접 흡수.
#   進化·意識은 매개 클러스터를 경유하므로 변①에서 제외 → C03 = 매개·직접 겹층.
DIRECT_KEEP = {("C13", "C06"), ("C14", "C06"),
               ("C02", "C03"), ("C06", "C03"), ("C07", "C03")}

RT_COLOR = {"1915↔개벽": "#e53e3e", "1924↔개벽": "#2b6cb0", "1915↔1924": "#805ad5",
            "1915↔월보": "#e53e3e", "1924↔월보": "#2b6cb0"}   # 월보=개벽과 동의미축


def to_year(d):
    if not d:
        return 9999
    y, m, *_ = d.split("-")
    return int(y) + (int(m) - 1) / 12


def fix_oldhangul(t):
    out, i = [], 0
    while i < len(t):
        ch = t[i]
        if 0x1100 <= ord(ch) <= 0x1112 and i + 1 < len(t) and ord(t[i + 1]) == 0x119E:
            L = ord(ch) - 0x1100
            T, adv = 0, 2
            if i + 2 < len(t) and 0x11A8 <= ord(t[i + 2]) <= 0x11C2:
                T, adv = ord(t[i + 2]) - 0x11A7, 3
            out.append(chr(0xAC00 + (L * 21 + 0) * 28 + T))
            i += adv
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def brief(title, n=13):
    import re
    t = (title or "").replace("教", "敎")
    t = fix_oldhangul(t)
    t = re.split(r"\s*[—–]", t)[0]
    t = re.sub(r"\([^)]*\)", "", t)
    t = re.split(r"[,=]", t)[0]
    t = t.strip()
    return (t[:n] + "…") if len(t) > n else t


def after_cutoff(meta, node):
    if node[0] not in ("개벽", "월보"):
        return False
    d = meta.get(node, ("", ""))[0]
    if not d:
        return False
    y, m, *_ = d.split("-")
    return (int(y), int(m)) > CUTOFF


def load_meta():
    meta = {}
    with open(HERE / "mag_meta.csv", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            meta[(r["src"], r["c"])] = (r["date"], r["title"])
    return meta


def select_edges(meta):
    # 3축(1915·개벽·1924) 축 간(inter) 관계 + 월보는 C72 노드만. 축내부(intra) 제거.
    by_rt = defaultdict(list)
    with open(HERE / "unit_sim.csv", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r["kind"] == "intra":
                continue
            a = (r["axisA"], r["unitA"])
            b = (r["axisB"], r["unitB"])
            if a[0] in ("개벽", "월보") and b[0] in ("개벽", "월보"):
                continue                       # 매개층 내부(개벽↔월보 등) = 경로 아님, 제외
            if "월보" in (a[0], b[0]) and WOLBO_CL not in (a, b):
                continue                       # 월보는 C72만 통과
            if after_cutoff(meta, a) or after_cutoff(meta, b):
                continue
            by_rt[r["reltype"]].append(
                dict(a=a, b=b, sim=float(r["sim"]), rt=r["reltype"], kind="inter"))
    kept = []
    for rt, es in by_rt.items():
        es.sort(key=lambda e: e["sim"], reverse=True)
        if rt == "1915↔1924":
            # 직접(변①)은 top-N이 아니라 DIRECT_KEEP 끝점만 명시 채택.
            for e in es:
                u15 = e["a"][1] if e["a"][0] == "1915" else e["b"][1]
                u24 = e["a"][1] if e["a"][0] == "1924" else e["b"][1]
                if (u15, u24) in DIRECT_KEEP and e["sim"] >= INTER_FLOOR:
                    kept.append(e)
            continue
        n = WOLBO_N if "월보" in rt else INTER_N
        kept += [e for e in es[:n] if e["sim"] >= INTER_FLOOR]

    #  · 1915→1924 직접 엣지는 DIRECT_KEEP 끝점만(종교비교→雜感, 實在·生命→哲理).
    #  · 개벽 C53(동시산출 자매): 1915→C53만 존치, C53→1924 제외.
    def keep(e):
        if e["rt"] == "1915↔1924":
            return True                # 변①은 select_edges의 DIRECT_KEEP에서 이미 선별
        if ("개벽", "C53") in (e["a"], e["b"]):
            return e["rt"] == "1915↔개벽"
        # 잡지 끝점은 클러스터 글만 — 비클러스터 개벽 글(예: C23)이 끌어들이는
        # off-story 1915 장(예: C21, 종교 일반어 중첩)을 함께 제거해 일관성 유지.
        for nd in (e["a"], e["b"]):
            if nd[0] == "개벽" and nd[1] not in CLUSTER:
                return False
        return True
    return [e for e in kept if keep(e)]


def main():
    meta = load_meta()
    edges = select_edges(meta)
    nodes = set()
    for e in edges:
        nodes.add(e["a"]); nodes.add(e["b"])
    print(f"채택 엣지 {len(edges)} · 노드 {len(nodes)}")
    from collections import Counter as _C
    cnt = _C(e["rt"] for e in edges)
    print("  유형별 개수(inter):")
    for rt in ["1915↔개벽", "1924↔개벽", "1915↔1924", "1915↔월보", "1924↔월보"]:
        print(f"    {rt:12} {cnt.get(rt, 0)}")

    # ── 노드 좌표 ── (월보 C72는 개벽 컬럼에 합쳐 연월 순 배치)
    Y_TOP, Y_BOT = 4.0, -4.0
    col_nodes = defaultdict(list)
    for n in nodes:
        col = "개벽" if n == WOLBO_CL else n[0]      # C72 → 매개(개벽) 컬럼
        col_nodes[col].append(n)
    pos = {}
    node_year = {}
    MIN_GAP = 0.85      # 같은 달·근접 노드 최소 세로 간격
    for axn, ns in col_nodes.items():
        if axn == "개벽":
            # 매개 컬럼: 발행 연월에 *비례*해 세로 배치(이른 글=위). 균등 분포 안 함 —
            # 1921초(C19·C22)·1922초(C43·C72)·1924(C53)가 시간 간격대로 무리진다.
            ns.sort(key=lambda n: (to_year(meta.get(n, ("", ""))[0]), n[1]))
            ds = [to_year(meta.get(n, ("", ""))[0]) for n in ns]
            dmin, dmax = min(ds), max(ds)
            rng = (dmax - dmin) or 1.0
            prev = None
            for n, d in zip(ns, ds):
                y = Y_TOP - (d - dmin) / rng * (Y_TOP - Y_BOT)
                if prev is not None and y > prev - MIN_GAP:
                    y = prev - MIN_GAP          # 너무 붙으면 최소 간격 확보
                prev = y
                pos[n] = (COLX[axn], y)
                node_year[n] = (meta.get(n, ("", ""))[0] or "")[:7]
        else:
            ns.sort(key=lambda n: n[1])
            k = len(ns)
            gap = (Y_TOP - Y_BOT) / max(k - 1, 1)
            for i, n in enumerate(ns):
                pos[n] = (COLX[axn], Y_TOP - i * gap)

    fig, ax = plt.subplots(figsize=(12, 8.6))

    HEAD = {"1915": "이노우에\n『哲學と宗敎』(1915-02)\n— 장(목차순)",
            "개벽": "이돈화\n: 매개 글(개벽·월보, 연월순)",
            "1924": "이돈화\n『人乃天要義』(1924-03)\n— 장(목차순)"}
    ytop = Y_TOP + 1.1
    for axn, x in COLX.items():
        ax.text(x, ytop, HEAD[axn], ha="center", va="bottom",
                fontsize=10.5, fontweight="bold", color="#1a202c")
        ax.axvline(x, color="#e2e8f0", lw=0.8, zorder=0)
    ax.text(COLX["개벽"], Y_TOP + 0.55, "매개", ha="center", va="center",
            fontsize=11, fontweight="bold", color="#b45309", zorder=9,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#dd6b20", lw=1.2))

    # ── inter 엣지 ──
    for e in edges:
        a, b = e["a"], e["b"]
        src, dst = (a, b) if RANK[a[0]] <= RANK[b[0]] else (b, a)
        (xa, ya), (xb, yb) = pos[src], pos[dst]
        span = RANK[dst[0]] - RANK[src[0]]
        rad = 0.04 + 0.05 * (span - 1)
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
        is_wolbo_cl = (n == WOLBO_CL)
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
        elif is_wolbo_cl:
            # 월보 매개 노드: 마름모 + 청록색 + (월보) 표식
            ax.scatter(x, y, s=140, marker="D", color="#0d9488",
                       edgecolors="white", linewidths=1.2, zorder=7)
            tt = brief(TITLE_FIX.get(n) or meta.get(n, ("", ""))[1])
            yr = node_year.get(n, "")
            ax.annotate(f"{tt} (월보 {c}, {yr})", (x, y), xytext=(x + 0.11, y),
                        ha="left", va="center", fontsize=8.6, fontweight="bold",
                        zorder=8, color="#0f766e")
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

    # ── 회수(回收) 라벨 ──
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
    ax.set_title("어휘 유사도 분포로 본 매개와 회수", fontsize=14, fontweight="bold", pad=16)

    leg = [
        Line2D([0], [0], color="#e53e3e", lw=2.6, label="1915→매개 (변②, 자원 유입)"),
        Line2D([0], [0], color="#2b6cb0", lw=2.6, label="매개→1924 (변③, 회수 도달)"),
        Line2D([0], [0], color="#805ad5", lw=2.6, label="1915 → 1924 (변①, 직접 흡수: 종교비교·哲理 實在/生命)"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#2b6cb0",
               markersize=9, label="매개 클러스터 글(개벽)"),
        Line2D([0], [0], marker="D", color="w", markerfacecolor="#0d9488",
               markersize=9, label="매개 클러스터 글(월보 C72)"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#d69e2e",
               markersize=9, label="'잡감'과 동시산출"),
    ]
    ax.legend(handles=leg, loc="upper left", bbox_to_anchor=(0.0, 0.05),
              fontsize=8.6, frameon=True, framealpha=0.95)

    fig.tight_layout()
    outdir = HERE.parent / "appendix"
    fig.savefig(outdir / "매개회수그림.svg", bbox_inches="tight")
    fig.savefig(outdir / "매개회수그림.png", dpi=190, bbox_inches="tight")
    print(f"saved {outdir / '매개회수그림.svg'} / .png")


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    main()
