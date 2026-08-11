# -*- coding: utf-8 -*-
"""(b) 표지-추적 파일럿 — 이돈화 잡지 160편(개벽74+월보86), 매체×연도별 표지율.

소스: norm/tokens_개벽.csv + tokens_월보.csv (비윈도우) / mag_meta.csv(연도·매체).
표지는 한자+한글 양형 합산. 3구분법은 청크 단위 3항 공기(종교∧철학∧과학|사회).
출력: 표 (월보 척추 1913-24 + 개벽 오버레이 1920-24). 단행본(1924)은 별도 잣대라 제외.
"""
import csv, sys
from collections import defaultdict
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")

NORM = Path(r"C:\hp_data\0_tnt\hyeonsang\_ocr_experiments\unified_db_2026-05-19\output\norm")
META = Path(__file__).parent / "mag_meta.csv"

# 표지: 개념 → 양형(한자/한글) 집합
F = {
    "종교": {"宗敎", "종교"}, "철학": {"哲學", "철학"},
    "과학": {"科學", "과학"}, "사회": {"社會", "사회"},
    "현상": {"現象", "현상"}, "실재": {"實在", "실재"}, "본체": {"本體", "본체"},
    "문화": {"文化", "문화"}, "개조": {"改造", "개조"}, "인격": {"人格", "인격"},
    "유물": {"唯物", "유물"}, "물질": {"物質", "물질"}, "계급": {"階級", "계급"},
}
GROUP = {  # 표지 계열 → 개념들 (bare-token 율)
    "ⓔ도식(현상·실재·본체)": ["현상", "실재", "본체"],
    "ⓒ문화개조(문화·개조·인격)": ["문화", "개조", "인격"],
    "ⓓ응전(유물·물질·계급)": ["유물", "물질", "계급"],
}

# 1) 메타: (src,c) → (year, venue)
meta = {}
with open(META, encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        meta[(r["src"], r["c"])] = (r["date"][:4], r["src"])

# 2) 토큰: 기사별 토큰 카운트 + 청크별 토큰 집합
art_tok = defaultdict(lambda: defaultdict(int))   # (src,c) -> token -> n
art_total = defaultdict(int)                       # (src,c) -> 총 토큰
chunk_set = defaultdict(set)                        # (src,c,nchunk) -> token set
for fn in ("tokens_개벽.csv", "tokens_월보.csv"):
    with open(NORM / fn, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            key = (r["src"], r["c"]); tok = r["token"]
            if not tok:
                continue
            art_tok[key][tok] += 1
            art_total[key] += 1
            chunk_set[(r["src"], r["c"], r["n_chunk_id"])].add(tok)

def cnt(toks, concept):
    return sum(toks.get(t, 0) for t in F[concept])

# 3) 매체×연도 집계
cell_tok = defaultdict(int)                          # (venue,year) -> 총 토큰
cell_marker = defaultdict(lambda: defaultdict(int))  # (venue,year) -> concept -> n
cell_art = defaultdict(int)                          # (venue,year) -> 기사수
for key, toks in art_tok.items():
    if key not in meta:
        continue
    yr, ven = meta[key]
    cell_tok[(ven, yr)] += art_total[key]
    cell_art[(ven, yr)] += 1
    for c in F:
        cell_marker[(ven, yr)][c] += cnt(toks, c)

# 3구분법 청크 공기: (venue,year) -> {'과학':n_chunks, '사회':n, 'tot':n_chunks}
tri = defaultdict(lambda: defaultdict(int))
for (src, c, _), s in chunk_set.items():
    if (src, c) not in meta:
        continue
    yr, ven = meta[(src, c)]
    tri[(ven, yr)]["tot"] += 1
    has_jong = bool(s & F["종교"]); has_chol = bool(s & F["철학"])
    if has_jong and has_chol and (s & F["과학"]):
        tri[(ven, yr)]["과학"] += 1
    if has_jong and has_chol and (s & F["사회"]):
        tri[(ven, yr)]["사회"] += 1

# 4) 출력
def years(ven):
    return sorted({y for (v, y) in cell_tok if v == ven})

for ven in ("월보", "개벽"):
    print(f"\n{'='*72}\n[{ven}]  (기사수 N · 총토큰 T · 1000토큰당 표지율)\n{'='*72}")
    hdr = "연도  N   T     " + "  ".join(f"{g[:8]:>8}" for g in GROUP)
    print(hdr)
    for y in years(ven):
        T = cell_tok[(ven, y)]; N = cell_art[(ven, y)]
        cells = []
        for g, concepts in GROUP.items():
            m = sum(cell_marker[(ven, y)][c] for c in concepts)
            cells.append(f"{1000*m/T:8.2f}" if T else "     n/a")
        print(f"{y}  {N:<3} {T:<5} " + "  ".join(cells))

print(f"\n{'='*72}\n[3구분법 청크 공기]  종교∧철학∧(과학 vs 사회), 100청크당\n{'='*72}")
for ven in ("월보", "개벽"):
    print(f"\n--{ven}--  연도  청크수   과학형/100   사회형/100")
    for y in years(ven):
        t = tri[(ven, y)]
        tot = t["tot"]
        if not tot:
            continue
        print(f"        {y}   {tot:<5}   {100*t['과학']/tot:8.2f}   {100*t['사회']/tot:8.2f}")

# 5) 그림 — 월보 척추(실선) + 개벽 오버레이(점선), 마커 크기 ∝ √기사수
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False
OUT = Path(__file__).parent.parent / "appendix"

def rate(concepts, ven, y):
    T = cell_tok[(ven, y)]
    return 1000 * sum(cell_marker[(ven, y)][c] for c in concepts) / T if T else None

PANELS = [
    ("ⓒ 문화개조 (문화·개조·인격)", ["문화", "개조", "인격"], "1920–21 급등 · 개벽>월보 (배치)"),
    ("ⓓ 응전 (유물·물질·계급)", ["유물", "물질", "계급"], "1922→ 상승 · 개벽 1924 정점"),
    ("ⓔ 도식 (현상·실재·본체)", ["현상", "실재", "본체"], "사회 국면에도 골 없음 → 연속 공동배치"),
]
VENSTYLE = {"월보": dict(color="#1f4e79", ls="-", marker="o"),
            "개벽": dict(color="#c0392b", ls="--", marker="s")}
fig, axes = plt.subplots(3, 1, figsize=(9.2, 9.6), sharex=True)
for ax, (title, concepts, note) in zip(axes, PANELS):
    ax.axvspan(1919.5, 1921.5, color="#fcf3d9", zorder=0)  # 사회개조 국면
    for ven in ("월보", "개벽"):
        ys = [y for y in years(ven) if 1911 <= int(y) <= 1926]
        xs = [int(y) for y in ys]
        rs = [rate(concepts, ven, y) for y in ys]
        sz = [18 + 9 * (cell_art[(ven, y)] ** 0.5) for y in ys]
        st = VENSTYLE[ven]
        ax.plot(xs, rs, color=st["color"], ls=st["ls"], lw=1.8, zorder=2, label=ven)
        ax.scatter(xs, rs, s=sz, color=st["color"], marker=st["marker"],
                   edgecolors="white", linewidths=0.6, zorder=3)
    ax.set_title(title, fontsize=11.5, fontweight="bold", loc="left")
    ax.text(0.99, 0.93, note, transform=ax.transAxes, ha="right", va="top",
            fontsize=9, color="#555", style="italic")
    ax.set_ylabel("1000토큰당", fontsize=9.5)
    ax.set_ylim(bottom=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
axes[0].legend(loc="upper left", fontsize=9.5, frameon=False,
               title="매체 (마커 크기 ∝ √기사수)", title_fontsize=8.5)
axes[-1].set_xlabel("연도", fontsize=10.5)
axes[-1].set_xticks(range(1911, 1927, 1))
axes[-1].tick_params(axis="x", labelrotation=0)
fig.suptitle("(b) 표지-추적 파일럿 — 이돈화 잡지 160편 (월보 척추 + 개벽 오버레이)\n"
             "노랑 띠 = 1920–21 사회개조 국면 · 단행본(1924)은 별도 잣대라 제외",
             fontsize=12.5, fontweight="bold", x=0.06, ha="left")
fig.tight_layout(rect=[0, 0, 1, 0.95], h_pad=1.8)
fig.savefig(OUT / "표지추적_파일럿.svg", bbox_inches="tight")
fig.savefig(OUT / "표지추적_파일럿.png", dpi=185, bbox_inches="tight")
print(f"\nsaved {OUT / '표지추적_파일럿.png'} / .svg")
