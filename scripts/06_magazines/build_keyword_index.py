# -*- coding: utf-8 -*-
"""월보 86편 키워드 색인 — 한 행이 한 출현.

왜
    저장소에 OCR이 전부 올라가 있는데도 「이 낱말이 언제 어디에 나오는가」를 말할 수
    없었다. 초벌 전사에는 마커가 낱말 한가운데를 지나 단순 검색이 과소 계수하고
    (`screening_1922.md` §2), 정본은 아홉 편뿐이라 전편을 같은 방식으로 셀 수 없었다.

방법
    **합의본(draft_v0)이 아니라 엔진 원출력을 센다.** 원출력에는 마커가 없고
    `[col NN]` 줄 표시가 붙어 있어 **출현 자리가 단·글줄 단위로 잡힌다.**
    같은 단에서 두 엔진이 함께 읽은 것은 한 행으로 묶어 `both`, 한쪽만 읽은 것은
    `claude_only`/`gemini_only`로 남긴다. 이것이 `engine_agreement_counts.py`의
    하한·상한을 **출현 자리 단위로 편 것**이다.

    정본이 있는 편(9편)은 엔진 원출력 대신 **정본 본문을 센다.** 사람이 지면과 대조해
    확정한 판이 있는데 기계 판독을 셀 까닭이 없다.

등급 (grade)
    정본    사람이 전문을 지면과 대조한 편에서 나온 출현 (9편)
    대조    그 자리를 원본 지면과 대조한 출현 (`screening_1922.md` §3-1, 10편 29자리)
    합의    두 엔진이 같은 단에서 함께 읽음 — 초벌이되 하한에 든다
    C단독   Claude만 읽음 — 상한에는 들되 하한에는 못 든다
    G단독   Gemini만 읽음 — 위와 같다

    ⚠️ **어느 등급도 「원문이 그렇다」를 뜻하지 않는다.** 두 엔진이 함께 틀리는 자리가
    있고, Gemini는 583단 중 89단이 빈 출력이다(그 구간의 「없음」은 「보지 않았음」이다).
    인용하려면 그 자리를 지면과 대조해야 한다(`verified_passages.md`).

한계
    - `唯物論`의 출현은 `唯物`에도 잡힌다. 낱말끼리 겹치는 것을 지우지 않는다.
    - 단(col) 번호는 엔진이 매긴 것이며 지면의 글줄 번호와 1:1이 아닐 수 있다.
    - 정본편의 행에는 단 번호가 없다(정본은 단을 보존하지 않는다). 대신 원문 쪽이 있다.

쓰기
    python3 scripts/06_magazines/build_keyword_index.py
    python3 scripts/06_magazines/build_keyword_index.py --terms 精神 物質 --out /tmp/x.csv
"""
import argparse
import csv
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
WOLBO = ROOT / 'data' / '5_magazine_sources' / 'wolbo'

TERMS_TRIAD = ['三派', '唯物論', '唯心論', '物心合一論', '唯物', '唯心', '實在', '物心']
TERMS_CORE = ['生命', '靈魂', '意識', '進化', '人乃天', '現象', '哲學', '科學', '宗敎']
DEFAULT_TERMS = TERMS_TRIAD + TERMS_CORE

CTX = 16  # 문맥 좌우 글자 수

# 정본 — 사람이 전문을 지면과 대조한 편. verified_transcripts/README.md §1.
VERIFIED_FULL = {
    1: 'articles/001_勸誘_1911-01/transcripts/article_01.high_fidelity.md',
    30: 'verified_transcripts/030_最高_1915-05.high_fidelity.md',
    31: 'verified_transcripts/031_篤心_1915-06.high_fidelity.md',
    32: 'verified_transcripts/032_人生_1915-08.high_fidelity.md',
    33: 'verified_transcripts/033_金剛_1915-09.high_fidelity.md',
    34: 'verified_transcripts/034_大宇_1915-10.high_fidelity.md',
    35: 'verified_transcripts/035_人生_1917-01.high_fidelity.md',
    36: 'verified_transcripts/036_是我_1917-11.high_fidelity.md',
    37: 'verified_transcripts/037_吾敎_1917-12.high_fidelity.md',
}

# 자리 대조 — 후보 10편의 3분법 계열 낱말 전 출현을 지면과 대조(2026-08-11).
# screening_1922.md §3-1. 대조한 것은 아래 (편, 낱말) 쌍뿐이며 다른 낱말은 대조 밖이다.
CROSS_CHECKED_DATE = '2026-08-11'
CROSS_CHECKED = {
    (12, '實在'), (19, '實在'), (23, '唯心'), (38, '唯心'), (39, '唯物'),
    (45, '實在'), (53, '實在'), (56, '實在'), (61, '實在'),
    (81, '唯物'), (81, '唯心'), (81, '物心'),
    (81, '唯物論'), (81, '唯心論'), (81, '物心合一論'),
}

TAG = re.compile(r'^\[(col\s*\d+|section|title|author|body|note|caption)\]\s*', re.I)
COL = re.compile(r'^\[col\s*(\d+)\]\s*(.*)$', re.I)
PAGE_MARK = re.compile(r'<(\d+)>')


def load_index():
    with open(WOLBO / 'series_index.csv', encoding='utf-8-sig') as f:
        return {int(r['series_index']): r for r in csv.DictReader(f)}


COLLAPSED = []   # 엔진이 무너진 단 — 집계에서 뺀 자리를 남긴다


def parse_units(adir, engine):
    """엔진 원출력을 {unit_id: [(col, text), ...]}로 읽는다."""
    d = adir / 'ocr' / engine
    out = {}
    if not d.is_dir():
        return out
    for f in sorted(d.glob('unit_*.txt')):
        cols, cur = [], None
        for line in f.read_text(encoding='utf-8', errors='ignore').splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            m = COL.match(line)
            if m:
                cur = [m.group(1).zfill(2), m.group(2)]
                cols.append(cur)
                continue
            if TAG.match(line):          # [title]·[author] 등 — 본문 아님
                cur = None
                continue
            if cur is not None:          # 줄바꿈으로 이어진 같은 단
                cur[1] += line
        out[f.stem] = [(c, re.sub(r'\s', '', t)) for c, t in cols if t.strip()]
    return out


def verified_body(path):
    """정본에서 프론트매터·머리글·태그를 걷고 본문만 돌려준다. <n>은 보존."""
    t = path.read_text(encoding='utf-8')
    t = re.sub(r'^---\n.*?\n---\n', '', t, flags=re.S)
    t = re.sub(r'^#.*$', '', t, flags=re.M)
    t = TAG.sub('', t)
    t = re.sub(r'^\[(section|title|author|body)\].*$', '', t, flags=re.M)
    return re.sub(r'\s', '', t)


def facsimile_body(adir):
    """영인·단일 전사본에서 본문만 돌려준다. 없으면 None.

    영인본 촬영을 **한 엔진**이 판독한 판이다. 대조 엔진이 없으므로 마커가 없고,
    따라서 정본과 같은 「단일 본문」 경로로 센다. 다만 **등급은 정본이 아니다** —
    마커의 부재가 일치의 증거가 아니라는 것을 grade 열이 밝힌다.
    """
    td = adir / 'transcripts'
    fs = sorted(td.glob('*.영인단일.md')) if td.is_dir() else []
    if not fs:
        return None
    t = fs[0].read_text(encoding='utf-8')
    t = re.sub(r'^---\n.*?\n---\n', '', t, flags=re.S)
    t = re.sub(r'^#.*$', '', t, flags=re.M)
    t = re.sub(r'^>.*$', '', t, flags=re.M)          # 등급 고지 인용문
    t = re.sub(r'^〔.*?〕\s*$', '', t, flags=re.M)     # 〔unit_NN · …〕 단 표시
    t = TAG.sub('', t)
    t = re.sub(r'^\[(section|title|author|body)\].*$', '', t, flags=re.M)
    return re.sub(r'\s', '', t)


def page_of(body, pos, start_page):
    """정본 본문에서 pos가 놓인 원문 쪽. <n>은 「여기까지가 n쪽」."""
    m = PAGE_MARK.search(body, pos)
    return m.group(1) if m else str(start_page) if start_page else ''


def ctx(text, s, e):
    return text[max(0, s - CTX):s], text[e:e + CTX]


def rows_for_article(n, meta_row, adir, terms, verified_path):
    """한 편의 출현 행들."""
    date, title = meta_row['publish_date'], meta_row['title']
    rows = []

    if verified_path is not None:
        body = verified_body(verified_path)
        clean = PAGE_MARK.sub('', body)     # 쪽 표시를 뺀 판에서 찾고
        mapping, skip = [], 0               # 그 자리를 원본 자리로 되짚는다
        for i, ch in enumerate(body):
            if skip:
                skip -= 1
                continue
            m = PAGE_MARK.match(body, i)
            if m:
                skip = len(m.group(0)) - 1
                continue
            mapping.append(i)
        for t in terms:
            for h in re.finditer(re.escape(t), clean):
                orig = mapping[h.start()] if h.start() < len(mapping) else 0
                left, right = ctx(clean, h.start(), h.end())
                rows.append(dict(
                    term=t, series=n, date=date, title=title,
                    journal_page=page_of(body, orig, meta_row.get('page_in_journal')),
                    unit='', col='', char_pos=h.start(),
                    engine_agreement='verified',
                    context_left=left, match=t, context_right=right,
                    grade='정본',
                    verified=f'Y 정본',
                ))
        return rows

    fb = facsimile_body(adir)
    if fb is not None:
        for t in terms:
            for h in re.finditer(re.escape(t), fb):
                left, right = ctx(fb, h.start(), h.end())
                rows.append(dict(
                    term=t, series=n, date=date, title=title,
                    journal_page=meta_row.get('page_in_journal', ''),
                    unit='', col='', char_pos=h.start(),
                    engine_agreement='single',
                    context_left=left, match=t, context_right=right,
                    grade='영인·단일',
                    verified='N 단일엔진',
                ))
        return rows

    # 🔴 기사 경계 밖(앞 기사 꼬리·다음 기사 머리·사진 캡션·란 이름)을 걷어낸 판이
    #    있으면 그것을 센다. 걷어내기 전 텍스트에는 남의 글 4만 자가 섞여 있어
    #    「이돈화의 글에 이 말이 몇 번」을 물으면 그만큼 더 세어진다.
    #    (2026-08-12 trim_article_bounds.py — 정본 8편에서 분량 +21.9% → −0.1%)
    def pick(name):
        tr = adir / 'ocr' / f'{name}_trimmed'
        return f'{name}_trimmed' if tr.is_dir() and any(tr.glob('*.txt')) else name
    cu = parse_units(adir, pick('claude_opus_4_7'))
    gu = parse_units(adir, pick('gemini'))
    meta = yaml.safe_load((adir / 'meta.yaml').read_text(encoding='utf-8'))
    unit_page = {u['id']: u.get('page', '') for u in meta.get('units', [])}
    jp = {}
    for p in (meta.get('ancillary') or {}).get('page_numbers', []) or []:
        jp[p.get('page')] = p.get('hanja', p.get('value'))

    for unit in sorted(set(cu) | set(gu)):
        page = unit_page.get(unit, '')
        gtext = ''.join(t for _, t in gu.get(unit, []))
        ctext = ''.join(t for _, t in cu.get(unit, []))

        # 🔴 엔진이 한 단에서 통째로 무너져 같은 말을 되뇌는 일이 있다
        #    (`_ruleset.md` §8-1 「엔진 실패편」). 2026-08-12에 #119 unit_8 에서
        #    Gemini가 50,776자를 뱉었고(Claude는 1,870자) 그 안에 靈魂이 994번
        #    들어 있었다. 그 한 단 때문에 코퍼스 전체의 靈魂이 36→1,059로
        #    **서른 배** 부풀었다. 색인에는 이것을 막을 장치가 없었다.
        #    한쪽이 다른 쪽의 세 배를 넘으면 **긴 쪽을 버린다** — 지면은 하나이므로
        #    분량이 세 배 차이 날 수 없다.
        if ctext and gtext and len(gtext) > 3 * len(ctext) + 300:
            COLLAPSED.append((adir.name, unit, 'gemini', len(gtext), len(ctext)))
            gtext = ''; gu[unit] = []
        elif ctext and gtext and len(ctext) > 3 * len(gtext) + 300:
            COLLAPSED.append((adir.name, unit, 'claude', len(ctext), len(gtext)))
            ctext = ''; cu[unit] = []
        for t in terms:
            # Claude는 글줄(col)을 그대로 뱉고 Gemini는 여러 글줄을 한 덩이로 뱉는다.
            # 따라서 짝짓기는 **단(col)이 아니라 unit 단위**로 한다. 같은 unit에서
            # 둘 다 k번 읽었으면 앞에서부터 k쌍을 both로 보고 나머지를 단독으로 남긴다.
            ch = [(col, h) for col, ct in cu.get(unit, [])
                  for h in re.finditer(re.escape(t), ct)]
            gh = list(re.finditer(re.escape(t), gtext))
            pair = min(len(ch), len(gh))
            items = []
            for col, h in ch[:pair]:
                items.append(('both', col, dict(cu.get(unit, []))[col], h))
            for col, h in ch[pair:]:
                items.append(('claude_only', col, dict(cu.get(unit, []))[col], h))
            for h in gh[pair:]:
                items.append(('gemini_only', '', gtext, h))
            for agree, col, src, h in items:
                left, right = ctx(src, h.start(), h.end())
                if (n, t) in CROSS_CHECKED:
                    grade, ver = '대조', f'Y {CROSS_CHECKED_DATE}'
                elif agree == 'both':
                    grade, ver = '합의', ''
                elif agree == 'claude_only':
                    grade, ver = 'C단독', ''
                else:
                    grade, ver = 'G단독', ''
                rows.append(dict(
                    term=t, series=n, date=date, title=title,
                    journal_page=jp.get(page, ''),
                    unit=unit, col=col, char_pos=h.start(),
                    engine_agreement=agree,
                    context_left=left, match=t, context_right=right,
                    grade=grade, verified=ver,
                ))
    return rows


FIELDS = ['term', 'series', 'date', 'title', 'journal_page', 'unit', 'col',
          'char_pos', 'engine_agreement', 'context_left', 'match',
          'context_right', 'grade', 'verified']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--terms', nargs='*', default=DEFAULT_TERMS)
    ap.add_argument('--out', default=str(WOLBO / 'keyword_index.csv'))
    args = ap.parse_args()

    index = load_index()
    dirs = {}
    for d in sorted((WOLBO / 'articles').iterdir()):
        m = re.match(r'(\d+)_', d.name)
        if d.is_dir() and m:
            dirs[int(m.group(1))] = d

    rows, missing = [], []
    for n in sorted(index):
        if n not in dirs:
            missing.append(n)
            continue
        vp = WOLBO / VERIFIED_FULL[n] if n in VERIFIED_FULL else None
        if vp is not None and not vp.exists():
            print(f'⚠️ 정본 없음: C{n} {vp}', file=sys.stderr)
            vp = None
        rows += rows_for_article(n, index[n], dirs[n], args.terms, vp)

    rows.sort(key=lambda r: (r['term'], r['date'], r['series'], r['unit'], r['col'],
                             r['char_pos']))
    out = Path(args.out)
    with open(out, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    print(f'{out} — {len(rows)}행')
    if missing:
        print(f'전사 없는 편: {", ".join(f"C{n}" for n in missing)} '
              f'(원본 지면은 있으나 OCR 미착수)')
    print()
    print(f'{"낱말":<12}{"행":>6}{"정본":>6}{"영인단일":>8}{"대조":>6}{"합의":>6}'
          f'{"C단독":>7}{"G단독":>7}{"편":>5}')
    for t in args.terms:
        rs = [r for r in rows if r['term'] == t]
        cnt = lambda g: sum(1 for r in rs if r['grade'] == g)
        print(f'{t:<12}{len(rs):>6}{cnt("정본"):>6}{cnt("영인·단일"):>8}{cnt("대조"):>6}'
              f'{cnt("합의"):>6}{cnt("C단독"):>7}{cnt("G단독"):>7}'
              f'{len({r["series"] for r in rs}):>5}')


# ── COLLAPSED 보고 ────────────────────────────────────────────────────────
def _report_collapsed():
    if not COLLAPSED:
        return
    print(f'\n🔴 엔진이 무너진 단 {len(COLLAPSED)}개 — 집계에서 뺐다 '
          f'(`_ruleset.md` §8-1 「엔진 실패편」)')
    for slug, unit, eng, big, small in sorted(COLLAPSED, key=lambda x: -x[3])[:15]:
        print(f'   {slug[:24]:<26} {unit:<14} {eng:<7} {big:>7,}자 (반대 엔진 {small:,}자)')


if __name__ == '__main__':
    main()
    _report_collapsed()

