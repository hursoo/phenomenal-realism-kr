# -*- coding: utf-8 -*-
"""**이 기사가 어디서 시작해 어디서 끝나는가** — 판독본에서 남의 글을 걷어낸다.

왜 (2026-08-12 밤, Soo의 지적에서)
    「이 상태로는 빈도든 뭐든 분석 대상으로 삼기 어렵다」 — 옳았다. 그런데 재어 보니
    **막고 있던 것은 판독 정확도가 아니었다.**

        정본 8편에 대고 잰 Claude 날판독 —  일치 90.7%,  **분량 +21.9%**

    글자는 열에 아홉을 맞히는데 **분량이 22퍼센트 부풀어 있었다.** 빈도를 세면 그만큼
    더 세어진다. 덤이 어디 있는지 위치를 재어 보니 —

        머리 11.6% · 꼬리 10.6% · 가운데 7.9%

    **넷 중 셋이 글의 앞뒤 바깥**이었다. 실제로 무엇이 들어왔는지 보면 의심의 여지가 없다.
    C30의 머리에는 앞 기사 꼬리와 란 이름이, 가운데에는 **같은 27쪽 하단에 앉은 다음 글
    「天人의 欲能者一本」**이, C37의 꼬리에는 사진 캡션 「新任敬道師」가 들어와 있었다.

    곧 **판독을 아무리 잘해도 줄지 않는다.** 단 이미지에 남의 글이 들어 있으니 모델은
    있는 것을 읽었을 뿐이다. 고칠 곳은 판독이 아니라 **경계**다.

무엇을 하나
    세로쓰기는 오른쪽에서 왼쪽으로 읽는다. 그러니 모든 단의 글줄을 **읽는 차례대로 한 줄로
    이어 놓으면**, 이 기사는 그 안의 한 구간이다.

        [앞 기사 꼬리] … [우리 제목] … [우리 본문] … [다음 글 제목] … [다음 기사]
                          └────────── 여기만 남긴다 ──────────┘

    시작은 **세 증거를 더해** 찾는다 — 판독본의 `[title]`/`[author]` 라벨, 목차의 제목,
    그리고 **필자명**(제목 바로 뒤 한두 줄에 온다). 합이 4점 이상일 때만 자른다.
    증거 하나로 자르면 본문을 잃는다 — 실제로 C37이 그렇게 94.5%에서 87.6%로 떨어졌다.

    끝은 **다음 글 제목**으로 찾는다(`article_end_audit.csv`의 `next_title`).
    필자를 모르므로 증거가 약하다. 3점 이상일 때만.

성적 (정본 8편, 2026-08-12)
        분량  +21.9% → **−0.1%**      일치  90.7% → **90.7%**
    여덟 중 일곱이 ±6% 안, 다섯은 ±3% 안. **본문은 한 글자도 잃지 않았다.**
    C36은 +38.1% → −2.2%.

한계
    - **C32는 못 자른다**(+16.1%). 다음 글이 諺文部라 목차 제목이 「觀」 한 글자로 잡힌다.
      諺文部는 쪽번호 계열이 따로라 오늘 낮 「끝 재기」에서도 같은 이유로 걸렸다.
    - 분량이 맞았다고 글자가 맞은 것은 아니다. **9%의 오독은 그대로다.** 다만
      **체계적으로 부풀던 편향이 사라졌다** — 「몇 번」에 오차는 남되 한쪽으로 쏠리지 않는다.
    - 쪽 번호로는 못 자른다. **다음 글이 우리 마지막 쪽에서 시작**하기 때문이다
      (📌 「끝 쪽은 다음 글 시작 쪽이다」 — 2026-08-12 낮에 확인).

쓰기
    python3 trim_article_bounds.py --report            # 무엇을 얼마나 자를지만
    python3 trim_article_bounds.py --apply             # ocr/<engine>_trimmed/ 로 씀
    python3 trim_article_bounds.py --score             # 정본 8편으로 채점
"""
import argparse
import csv
import difflib
import re
from pathlib import Path

WB = Path('/home/creta/work/0_tnt/hyeonsang/_ocr_experiments/cheondogyo_wolbo_series')
REPO = Path(__file__).resolve().parents[2] / 'data' / '5_magazine_sources' / 'wolbo'

HEAD_MIN = 4     # 시작 경계를 인정하는 최소 점수 (제목3 + 필자2, 또는 라벨2 + 제목약1 …)
TAIL_MIN = 3     # 끝 경계. 증거가 약하므로 낮되, 낮은 만큼 창을 좁게 잡는다


def N(s):
    return re.sub(r'[\s、,。．\.]', '', s or '')


def units_of(d):
    """🔴 파일 이름을 사전순으로 정렬하면 unit_10 이 unit_1 보다 앞에 온다.
    단이 10개 넘는 편에서 순서가 뒤집혀 채점이 28%까지 무너졌다(2026-08-12)."""
    return sorted(d.glob('*.txt'),
                  key=lambda p: int(re.match(r'unit_(\d+)', p.stem).group(1)))


def seq(files):
    """모든 단의 글줄을 **읽는 차례대로** 한 줄로 잇는다. (kind, text, unit_stem)

    ⚠️ 라벨이 홀로 한 줄을 차지하고 본문이 다음 줄에 오는 판독본이 있다(C32·C33).
    그때 둘을 합치지 않으면 글줄 수가 두 배가 되고 제목이 잡히지 않는다.
    """
    out = []
    for p in files:
        pend = None
        for line in p.read_text(encoding='utf-8').splitlines():
            if line.startswith('#') or not line.strip():
                continue
            m = re.match(r'\[([a-z_]+)[^\]]*\]\s*(.*)$', line)
            if m:
                k = m.group(1)
                k = 'col' if k == 'col' else ('next' if k.startswith('next') else k)
                if pend:
                    out.append(pend); pend = None
                if m.group(2).strip():
                    out.append((k, m.group(2), p.stem))
                else:
                    pend = (k, '', p.stem)
            else:
                if pend:
                    out.append((pend[0], line, p.stem)); pend = None
                else:
                    out.append(('col', line, p.stem))
        if pend:
            out.append(pend)
    return out


def score_at(items, j, title, author):
    """이 자리가 기사 경계일 근거를 점수로. **증거를 더해야 한다** — 하나로는 오절단한다."""
    kind, text = items[j][0], items[j][1]
    s, t, a = N(text), N(title), N(author or '')
    pts = 0
    if t and len(t) >= 3:
        m = difflib.SequenceMatcher(None, t, s[:len(t) + 10], autojunk=False)
        hit = sum(b.size for b in m.get_matching_blocks())
        if hit >= max(3, len(t) * 0.75):
            pts += 3
        elif hit >= max(3, len(t) * 0.5):
            pts += 1
    if kind == 'title':
        pts += 2
    if kind in ('author', 'next'):
        pts += 2
    if a and len(a) >= 2:                       # 필자는 제목 바로 뒤 한두 줄에 온다
        for d in (0, 1, 2):
            if j + d < len(items) and a in N(items[j + d][1])[:12]:
                pts += 2
                break
    return pts


def cut_points(items, title, author, next_title):
    hi = min(len(items), max(10, len(items) // 2))     # 제목이 뒤늦게 오는 편이 있다(C36: 29번째)
    best = max((score_at(items, j, title, author), -j, j) for j in range(hi))
    start = best[2] if best[0] >= HEAD_MIN else 0

    end = len(items)
    if next_title and len(N(next_title)) >= 3:
        lo = max(start + 1, len(items) - max(8, len(items) // 4))
        cand = [(score_at(items, j, next_title, ''), -j, j) for j in range(lo, len(items))]
        if cand:
            b = max(cand)
            if b[0] >= TAIL_MIN:
                end = b[2]
    return start, end


def load_tables():
    idx = {int(r['series_index']): r for r in
           csv.DictReader(open(WB / 'series_index.csv', encoding='utf-8-sig'))}
    ae, cat = {}, {}
    p = REPO / 'article_end_audit.csv'
    if p.exists():
        ae = {int(r['series']): r for r in csv.DictReader(p.open(encoding='utf-8-sig'))}
    p = REPO / 'CATALOG.csv'
    if p.exists():
        cat = {int(r['series']): r for r in csv.DictReader(p.open(encoding='utf-8-sig'))}
    return idx, ae, cat


def gold_text(p):
    t = Path(p).read_text(encoding='utf-8')
    t = re.sub(r'^---\n.*?\n---\n', '', t, flags=re.S)
    i = t.find('[body]')
    t = t[i + 6:] if i >= 0 else t
    m = re.search(r'^##\s', t, re.M)
    if m:
        t = t[:m.start()]
    return re.sub(r'[\s、,。．\.<>\d`?]', '', t)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--engine', default='claude_opus_4_7')
    ap.add_argument('--other', default='',
                    help='붕괴 판별에 쓸 반대 엔진. 한쪽이 3배를 넘으면 그 단을 뺀다')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--report', action='store_true')
    ap.add_argument('--score', action='store_true')
    args = ap.parse_args()
    idx, ae, cat = load_tables()

    if args.score:
        import statistics as st
        rows = []
        for f in sorted((WB / 'wolbo54_review_workbench').glob('*.high_fidelity.md')):
            n = int(f.name.split('_')[0])
            ds = list((WB / 'articles').glob(f'{n:02d}_*/ocr/{args.engine}'))
            if not ds:
                continue
            g = gold_text(f)
            items = seq(units_of(ds[0]))
            b0 = N('\n'.join(x[1] for x in items if x[0] == 'col'))
            s, e = cut_points(items, idx.get(n, {}).get('title', ''),
                              cat.get(n, {}).get('author', ''),
                              ae.get(n, {}).get('next_title', ''))
            b1 = N('\n'.join(x[1] for x in items[s:e] if x[0] == 'col'))
            f_ = lambda b: sum(x.size for x in difflib.SequenceMatcher(  # noqa: E731
                None, g, b, autojunk=False).get_matching_blocks()) / len(g) * 100
            rows.append((n, len(g), len(b0)/len(g)*100-100, len(b1)/len(g)*100-100, f_(b0), f_(b1)))
            print(f'{n:>4}{len(g):>7}{rows[-1][2]:>+8.1f}%{rows[-1][3]:>+8.1f}%'
                  f'{rows[-1][4]:>8.1f}%{rows[-1][5]:>8.1f}%')
        print(f'\n분량 {st.mean(r[2] for r in rows):+.1f}% → {st.mean(r[3] for r in rows):+.1f}%'
              f'  ·  일치 {st.mean(r[4] for r in rows):.1f}% → {st.mean(r[5] for r in rows):.1f}%')
        return

    made = cut = 0
    collapsed_units = []
    for d in sorted((WB / 'articles').iterdir()):
        m = re.match(r'(\d+)_', d.name)
        eng = d / 'ocr' / args.engine
        if not (m and eng.is_dir()):
            continue
        n = int(m.group(1))
        files = units_of(eng)
        if not files:
            continue
        items = seq(files)
        s, e = cut_points(items, idx.get(n, {}).get('title', ''),
                          cat.get(n, {}).get('author', ''),
                          ae.get(n, {}).get('next_title', ''))
        dropped = sum(len(N(x[1])) for x in items[:s] + items[e:] if x[0] == 'col')
        total = sum(len(N(x[1])) for x in items if x[0] == 'col')
        if args.report:
            if s or e < len(items):
                print(f'  #{n:<4} {d.name[:24]:<26} 앞{s:>3} 뒤{len(items)-e:>3} '
                      f'글줄 · {dropped:>5}자 ({dropped/max(total,1)*100:4.1f}%) 걷어냄')
        # 🔴 엔진이 한 단에서 무너져 같은 말을 되뇌는 일이 있다(`_ruleset.md` §8-1).
        #    2026-08-12에 #119 unit_8 에서 Gemini가 50,776자를 뱉었고(Claude 1,870자)
        #    그 한 단이 코퍼스 전체 靈魂 수치를 서른 배로 만들었다. 같은 지면이니
        #    분량이 3배 차이 날 수 없다 — 긴 쪽을 통째로 뺀다.
        bad = set()
        if args.other:
            od = d / 'ocr' / args.other
            if od.is_dir():
                for f in files:
                    of = od / f.name
                    if not of.exists():
                        continue
                    a = len(N(f.read_text(encoding='utf-8')))
                    b = len(N(of.read_text(encoding='utf-8')))
                    if b and a > 3 * b + 300:
                        bad.add(f.stem); collapsed_units.append((d.name, f.stem, a, b))

        if args.apply:
            out = d / 'ocr' / f'{args.engine}_trimmed'
            out.mkdir(parents=True, exist_ok=True)
            keep = items[s:e]
            by_unit = {}
            for k, t, u in keep:
                by_unit.setdefault(u, []).append((k, t))
            for f in files:
                if f.stem in bad:      # 무너진 단 — 빈 파일로 둔다. 없는 것이 낫다
                    (out / f.name).write_text(
                        f'# {args.engine} — 🔴 이 단은 엔진이 무너져(반대 엔진의 3배 초과) 뺐다\n',
                        encoding='utf-8')
                    continue
                lines = [f'# {args.engine} — 기사 경계 밖을 걷어낸 판({Path(__file__).name})',
                         f'# Source: {f.name}', '']
                for i, (k, t) in enumerate(by_unit.get(f.stem, []), 1):
                    lines.append(f'[col {i:02d}] {t}' if k == 'col' else f'[{k}] {t}')
                (out / f.name).write_text('\n'.join(lines) + '\n', encoding='utf-8')
            made += 1
        cut += dropped
    if collapsed_units:
        print(f'🔴 엔진이 무너져 뺀 단 {len(collapsed_units)}개')
        for slug, u, a, b in sorted(collapsed_units, key=lambda x: -x[2])[:6]:
            print(f'   {slug[:24]:<26} {u:<14} {a:>7,}자 (반대 {b:,}자)')
    if args.apply:
        print(f'{made}편 → ocr/{args.engine}_trimmed/ · 걷어낸 글자 {cut:,}')
    elif args.report:
        print(f'\n걷어낼 글자 합계 {cut:,}')


if __name__ == '__main__':
    main()
