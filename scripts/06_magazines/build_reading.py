# -*- coding: utf-8 -*-
"""읽을 수 있는 본문 86편 — 마커를 해소하되 해소 방식을 글자마다 표시한다.

왜
    저장소에 전사가 다 올라가 있는데도 읽히지 않았다. 초벌본은 엔진이 갈린 자리를
    `⚠️[C:…|G:…]`로 남긴 판이라 문장이 끊긴다. 완성될 때까지 기다리지 않고
    **미완인 채로 읽을 수 있게** 내놓되, 어디가 어느 등급인지 눈에 보이게 한다.

표시
    표시 없음   두 엔진이 애초에 같이 읽은 자리 — 마커가 서지 않았다. **미검수다**
    〔규칙〕     `_ruleset.md` §2·§3의 정자표·공백 규칙으로 해소 — 판단 불필요
    〔대장〕     정본에서 사람이 같은 갈림을 이미 정했다(`marker_decisions.csv`).
               그 결정을 옮긴 것이며 **이 자리를 본 것은 아니다**
    〔C〕〔G〕   규칙 밖. 그 엔진의 판독을 그대로 썼다. **기계가 고른 것이다**
    〔?C:…|G:…〕 대분기(§8) — 문단째 갈렸다. 고르지 않고 둘 다 남긴다
    〔확인〕     그 자리를 원본 지면과 대조했다(`screening_1922.md` §3-1)
    <n>        원문 쪽 경계. 앞이 n쪽이다

    정본 9편은 마커가 없으므로 표시도 없다. 파일 이름이 `.정본.md`다.

지켜야 할 것
    - `reading/`은 **파생물**이다. 낡으면 고치지 말고 다시 생성한다.
    - 초벌 원본(`articles/`)을 덮지 않는다.
    - 자동 해소한 것을 「확인」이라 부르지 않는다.

쓰기
    python3 scripts/06_magazines/build_reading.py
"""
import csv
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_keyword_index import CROSS_CHECKED, CROSS_CHECKED_DATE, VERIFIED_FULL  # noqa: E402
from wolbo_markers import GRADES, MARKER, counts, load_ledger, resolve, tag  # noqa: E402
from trim_article_bounds import (  # noqa: E402
    N as _N, cut_points as _cut, load_tables as _tables, seq as _seq, units_of as _units)


def _trim_body(body, adir, n, tabs):
    """초벌본 본문에서 **기사 경계 밖**을 걷어낸다.

    경계는 이미 `trim_article_bounds.py`가 엔진 판독(글줄 단위)에서 찾아 두었다.
    문제는 초벌본이 글줄로 나뉘어 있지 않고 **마커가 박힌 연속된 문자열**이라는 것.

    그래서 이렇게 한다 — 본문을 한 글자씩 훑으며 **C쪽 평문**을 만들되 각 글자가
    원문의 몇 번째에서 왔는지 **표를 함께 만든다.** 그러면 평문에서 찾은 자리를
    원문 자리로 **표 조회**로 바꿀 수 있다. 되짚기가 아니다.
    """
    idx, ae, cat = tabs
    eng = adir / 'ocr' / 'claude_opus_4_7'
    if not eng.is_dir():
        return body, 0
    items = _seq(_units(eng))
    s, e = _cut(items, idx.get(n, {}).get('title', ''),
                cat.get(n, {}).get('author', ''), ae.get(n, {}).get('next_title', ''))
    if s == 0 and e == len(items):
        return body, 0
    head = _N(''.join(x[1] for x in items[s:] if x[0] == 'col'))[:40]
    tail = _N(''.join(x[1] for x in items[:e] if x[0] == 'col'))[-40:]

    # C쪽 평문 + 위치표.
    # ⚠️ 마커에서 나온 글자는 원문에서 **구간**을 차지한다. 시작만 들고 있으면
    #    꼬리를 되돌릴 때 그 마커가 통째로 잘려 나간다(2026-08-13에 겪음 —
    #    판독 층보다 6~36%p 더 잘렸다). 시작과 끝을 **둘 다** 들고 간다.
    plain, span, i = [], [], 0
    for m in MARKER.finditer(body):
        for k, ch in enumerate(body[i:m.start()]):
            if not ch.isspace():
                plain.append(ch); span.append((i + k, i + k + 1))
        for ch in m.group(1):
            if not ch.isspace():
                plain.append(ch); span.append((m.start(), m.end()))
        i = m.end()
    for k, ch in enumerate(body[i:]):
        if not ch.isspace():
            plain.append(ch); span.append((i + k, i + k + 1))
    P = ''.join(plain)

    a = P.find(head) if head else -1
    b = P.rfind(tail) if tail else -1
    if a < 0 and b < 0:
        return body, 0
    lo = span[a][0] if a >= 0 else 0
    hi = span[b + len(tail) - 1][1] if b >= 0 else len(body)
    if hi <= lo:
        return body, 0
    return body[lo:hi], len(body) - (hi - lo)

ROOT = Path(__file__).resolve().parents[2]
WOLBO = ROOT / 'data' / '5_magazine_sources' / 'wolbo'
OUT = WOLBO / 'reading'

WARN = (
    '> ⚠️ **미검수.** 이 본문은 두 엔진(Claude·Gemini)의 판독을 기계가 해소한 것이며 '
    '사람이 지면과 대조하지 않았다.\n'
    '> 〔C〕〔G〕는 **기계가 한쪽을 고른 자리**이고, 〔?…〕는 **고르지 못한 자리**다. '
    '표시가 없는 대목도 두 엔진이 함께 틀렸을 수 있다.\n'
    '> 인용하려면 그 자리를 [`../source_pages/`](../source_pages/)의 원본 지면과 대조하고 '
    '[`../verified_passages.md`](../verified_passages.md)에 기록한다. '
    '읽는 법은 [`../TRUST.md`](../TRUST.md).'
)

WARN_VERIFIED = (
    '> ✅ **정본.** 사람이 전문을 원본 지면과 대조해 확정한 판이다'
    '([`../verified_transcripts/README.md`](../verified_transcripts/README.md)). '
    '이 파일은 그 정본의 사본이며 판본의 권위는 원본 쪽에 있다.'
)


def frontmatter(d):
    return '---\n' + yaml.dump(d, allow_unicode=True, sort_keys=False).rstrip() + '\n---\n'


def body_of(text):
    """전사본에서 `[body]` 이후 본문만 꺼낸다."""
    i = text.find('[body]')
    if i < 0:
        i = text.find('## 본문')
        i = 0 if i < 0 else i + len('## 본문')
    else:
        i += len('[body]')
    return text[i:].strip()


def mark_verified(body, terms):
    """대조를 마친 낱말의 출현에 〔확인〕을 붙인다.

    등급 표시가 낱말 한가운데를 지나는 경우(`唯心〔C〕論`)까지 잡되, **긴 낱말을 먼저
    잡고 그 안에 든 짧은 낱말은 건너뛴다.** 그러지 않으면 `唯心論`이
    `唯心〔확인〕論〔확인〕`이 된다.
    """
    spans = []
    for t in sorted(terms, key=len, reverse=True):
        pat = '(?:〔[^〕]*〕)?'.join(re.escape(c) for c in t)
        for m in re.finditer(pat, body):
            if any(s < m.end() and m.start() < e for s, e in spans):
                continue
            spans.append((m.start(), m.end()))
    for _, e in sorted(spans, key=lambda x: -x[1]):
        body = body[:e] + '〔확인〕' + body[e:]
    return body


def render_draft(raw, section, pagemap, vterms, ledger):
    """초벌본 → 등급 표시가 붙은 읽기 본문."""
    out, last = [], 0
    for m in MARKER.finditer(raw):
        out.append(raw[last:m.start()])
        text, grade = resolve(m.group(1), m.group(2), section, pagemap, ledger)
        out.append(tag(text, grade))
        last = m.end()
    out.append(raw[last:])
    body = ''.join(out)
    body = re.sub(r'\n{3,}', '\n\n', body).strip()
    if vterms:
        body = mark_verified(body, vterms)
    return body


TRIM_LOG = []
TABS = None


def main():
    global TABS
    TABS = _tables()
    ledger = load_ledger(WOLBO / 'marker_decisions.csv')
    print(f'결정 대장 {len(ledger)}쌍 (marker_decisions.csv에서 사람의 결정이 하나로 모이는 것만)')
    OUT.mkdir(exist_ok=True)
    for f in OUT.glob('*.md'):
        f.unlink()

    with open(WOLBO / 'series_index.csv', encoding='utf-8-sig') as f:
        index = {int(r['series_index']): r for r in csv.DictReader(f)}
    dirs = {}
    for d in sorted((WOLBO / 'articles').iterdir()):
        m = re.match(r'(\d+)_', d.name)
        if d.is_dir() and m:
            dirs[int(m.group(1))] = d

    made, stats = [], []
    for n, row in sorted(index.items()):
        adir = dirs.get(n)
        slug = adir.name if adir else f'{n:02d}_新年_{row["publish_date"][:7]}'
        vterms = sorted({t for s, t in CROSS_CHECKED if s == n})

        base = dict(
            type='reading', series_index=n, publish_date=row['publish_date'],
            tonggwon=row['tonggwon'], section=row['section'], title=row['title'],
            page_in_journal=row['page_in_journal'], cnts_id=row['cnts_id'],
        )

        if adir is None:                       # 전사가 아직 없는 편
            fm = dict(base, status='전사없음',
                      note='원본 지면은 있으나 OCR·전사를 아직 하지 않았다.')
            txt = (frontmatter(fm) + f'\n# {row["title"]} — 전사 없음\n\n'
                   f'> 이 편은 **아직 전사하지 않았다.** 원본 지면만 있다.\n'
                   f'> 지면은 [`../source_pages/{slug}/`]'
                   f'(../source_pages/{slug}/)에 있다.\n'
                   f'> **「86편에 없다」고 말할 때 이 한 편은 찾아본 적이 없는 편이다.**\n')
            path = OUT / f'{slug}.reading.전사없음.md'
            path.write_text(txt, encoding='utf-8')
            stats.append(dict(series=n, status='전사없음', 마커=0,
                              **{g: 0 for g in GRADES}))
            made.append(path)
            continue

        meta = yaml.safe_load((adir / 'meta.yaml').read_text(encoding='utf-8'))
        section = (meta.get('ancillary') or {}).get('section_label') or row['section']
        pagemap = {p.get('value'): p.get('hanja')
                   for p in ((meta.get('ancillary') or {}).get('page_numbers') or [])}
        author = (meta.get('article') or {}).get('author', '')

        if n in VERIFIED_FULL:                 # 정본 — 기계가 손댈 것이 없다
            src = WOLBO / VERIFIED_FULL[n]
            body = body_of(src.read_text(encoding='utf-8'))
            if vterms:
                body = mark_verified(body, vterms)
            fm = dict(base, author=author, status='정본',
                      source=str(src.relative_to(WOLBO)),
                      grade_note='사람이 전문을 지면과 대조했다. 마커 없음.')
            txt = (frontmatter(fm) + f'\n# {row["title"]} — 읽기용 (정본)\n\n'
                   + WARN_VERIFIED + '\n\n## 본문\n\n' + body + '\n')
            path = OUT / f'{slug}.reading.정본.md'
            stats.append(dict(series=n, status='정본', 마커=0,
                              **{g: 0 for g in GRADES}))
        else:                                  # 초벌 — 해소하고 등급을 남긴다
            draft = next(iter(sorted((adir / 'transcripts').glob('*.draft_v0.md'))), None)
            if draft is None:
                print(f'⚠️ 초벌 없음: C{n}', file=sys.stderr)
                continue
            raw = draft.read_text(encoding='utf-8')
            # 기사 경계 밖(앞 기사 꼬리·다음 기사 머리·사진 캡션)을 걷어낸다
            trimmed, dropped = _trim_body(body_of(raw), adir, n, TABS)
            TRIM_LOG.append((n, slug, dropped))
            c = counts(trimmed, section, pagemap, ledger)
            body = render_draft(trimmed, section, pagemap, vterms, ledger)
            fm = dict(
                base, author=author, status='미검수',
                source=str(draft.relative_to(WOLBO)),
                markers=c['마커'],
                grade_counts={g: c[g] for g in GRADES},
                auto_ratio=(round(100 * (c['규칙'] + c['대장']) / c['마커'], 1)
                            if c['마커'] else 0.0),
                cross_checked_terms=vterms,
            )
            txt = (frontmatter(fm) + f'\n# {row["title"]} — 읽기용 (미검수)\n\n'
                   + WARN + '\n\n' + grade_table(c) + '\n## 본문\n\n' + body + '\n')
            path = OUT / f'{slug}.reading.미검수.md'
            stats.append(dict(series=n, status='미검수', 마커=c['마커'],
                              **{g: c[g] for g in GRADES}))

        path.write_text(txt, encoding='utf-8')
        made.append(path)

    print(f'{OUT} — {len(made)}편')
    tot = {k: sum(s.get(k, 0) for s in stats) for k in ('마커',) + GRADES}
    print('마커 ' + str(tot['마커']) + ' = '
          + ' + '.join(f'{g} {tot[g]}' for g in GRADES))
    if tot['마커']:
        print(f'판단 불필요(규칙·대장) {100 * (tot["규칙"] + tot["대장"]) / tot["마커"]:.1f}% · '
              f'기계 선택(C·G) {100 * (tot["C"] + tot["G"]) / tot["마커"]:.1f}% · '
              f'미해소 {100 * tot["미해소"] / tot["마커"]:.1f}%')


def grade_table(c):
    if not c['마커']:
        return ''
    pc = lambda k: f'{100 * c[k] / c["마커"]:.1f}%'
    return (
        '| 등급 | 자리 | 비율 |\n|---|---:|---:|\n'
        f'| 〔규칙〕 정자표·공백 — 판단 불필요 | {c["규칙"]} | {pc("규칙")} |\n'
        f'| 〔대장〕 정본의 사람 결정을 옮김 | {c["대장"]} | {pc("대장")} |\n'
        f'| 〔C〕 Claude 판독을 그대로 | {c["C"]} | {pc("C")} |\n'
        f'| 〔G〕 Gemini 판독을 그대로 | {c["G"]} | {pc("G")} |\n'
        f'| 〔?…〕 대분기 — 고르지 못함 | {c["미해소"]} | {pc("미해소")} |\n'
        f'| 면주·면번호 분리 | {c["면주"]} | {pc("면주")} |\n'
        f'| **마커 합** | **{c["마커"]}** | |\n\n'
    )


if __name__ == '__main__':
    main()
