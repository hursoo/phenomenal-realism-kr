# -*- coding: utf-8 -*-
"""**NL로 닫히지 않는 편을 두 목록으로 뽑는다.**

왜
    `audit_article_end.py`가 「끝을 모르는」 85편을 냈고, `fetch_next_article_pages.py`가
    다음 글 지면을 받아 그 가운데 다수를 닫았다. **남은 것이 문제다.**

    남은 까닭이 한 가지가 아니다. 어떤 것은 NL이 그 기사를 등재하지 않았고, 어떤 것은
    지면 자체가 우리에게 없으며, 어떤 것은 목차의 쪽번호 계열이 달라 잴 수가 없다.
    **까닭이 다르면 할 일이 다르다.** 그래서 갈라 놓는다.

    ① `pending_nl.md`        — NL에서 다음 글을 못 찾은 편. 왜 못 찾았는지까지
    ② `pending_facsimile.md` — **영인본 실물을 봐야 닫히는 편.** 책 번호를 붙인다

    ②에 책 번호를 붙이는 것이 요점이다. 「영인본을 보라」는 말은 26책 앞에서 쓸모가 없다.
    「제12책을 펴라」여야 사람이 움직인다. 영인본 목차집의 `issues/<통권>.json`에
    `source_book`이 있어 통권 → 책이 바로 나온다.

무엇이 ②에 오르나
    - NL에서 다음 글을 못 찾아 끝을 못 닫는 편
    - 지면 자체가 결락된 편 (`지면결락N면`)
    - 목차의 쪽번호 계열이 달라 잴 수 없는 편 (諺文部 등 `계열바뀜`)
    - 그 호 목차의 마지막 항목이라 견줄 상대가 없는 편 (`다음없음`)

쓰기
    python3 build_pending_lists.py
"""
import csv
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2] / 'data' / '5_magazine_sources' / 'wolbo'
MOKROOT = Path('/mnt/e/#DT_DATA_all/0_srh/magazine/cheondo-weolbo/raw/moklok_facs')


def book_of(tonggwon):
    """통권 → 영인본 책 번호. 목차집의 호별 메타에 `source_book`이 있다."""
    p = MOKROOT / 'issues' / f'{int(tonggwon):03d}.json'
    if not p.exists():
        return None
    try:
        return json.load(p.open(encoding='utf-8')).get('source_book')
    except Exception:                                   # noqa: BLE001
        return None


def why(row):
    """못 찾은 까닭을 셋으로 가른다. 까닭이 다르면 할 일이 다르다."""
    t = row.get('next_title', '')
    if t in ('詞藻', '格言', '中央總部彙報', '還元一束', '地方消息', '寫眞'):
        return '고정란', 'NL이 기사 단위로 등재하지 않는 종류다'
    if re.search(r'\(續\)|其[一二三四五六七八九十\d]|\(\s*[一二三四五六七八九十\d]+\s*\)', t):
        return '연재 동명', '같은 제목이 여러 호에 걸쳐 있어 그 호의 것을 집어내지 못했다'
    return '그 호만 미등재', 'NL은 기사 단위로 등재하며 어떤 기사는 아예 없다'


def main():
    audit = {int(r['series']): r for r in csv.DictReader(
        (REPO / 'article_end_audit.csv').open(encoding='utf-8-sig'))}
    mapped = {int(r['series']): r for r in csv.DictReader(
        (REPO / 'next_article_map.csv').open(encoding='utf-8-sig'))}

    missed = [r for r in mapped.values() if not r['next_cnts']]
    missed.sort(key=lambda r: int(r['series']))

    # ① NL에서 못 찾은 편
    md = ['---', 'type: reference', 'created: 2026-08-12', 'updated: 2026-08-12',
          'tags: [천도교회월보, 미해결]', '---', '',
          '# NL에서 다음 글을 못 찾은 편', '',
          '이 편들은 **끝이 어디인지 아직 모른다.** 목차의 다음 글 시작 쪽이 우리 마지막',
          '보유 쪽보다 뒤에 있어 꼬리가 넘어갔을 수 있는데, 그 다음 글의 지면을 국립중앙',
          '도서관에서 받지 못했다.', '',
          '이 문서는 **파생물**이다. 고치지 말고 다시 생성한다.',
          '```bash', 'python3 scripts/06_magazines/build_pending_lists.py', '```', '',
          '**목차가 틀린 것이 아니다.** 열한 자리를 손으로 대조해 보니 목차·필자·쪽이',
          '앞뒤 항목과 매끄럽게 이어졌다(통93처럼 밀린 자리가 아니다). 걸린 것은 NL 쪽이다.', '',
          f'**{len(missed)}편**', '',
          '| 편 | 통권 | 발행 | 우리 글 | 보유 끝 | 찾으려던 다음 글 | 그 쪽 | 왜 못 찾았나 |',
          '|---:|---:|---|---|---:|---|---:|---|']
    tally = {}
    for r in missed:
        kind, _ = why(r)
        tally[kind] = tally.get(kind, 0) + 1
        md.append(f"| {r['series']} | {r['tonggwon']} | {r['publish_date'][:7]} | "
                  f"{r['title'][:20]} | {r['last_held']} | {r['next_title'][:24]} | "
                  f"{r['next_page']} | {kind} |")
    md += ['', '## 까닭별', '', '| 까닭 | 편수 | 뜻 |', '|---|---:|---|']
    seen = {}
    for r in missed:
        k, d = why(r)
        seen[k] = d
    for k in sorted(tally, key=lambda k: -tally[k]):
        md.append(f'| {k} | {tally[k]} | {seen[k]} |')
    (REPO / 'pending_nl.md').write_text('\n'.join(md) + '\n', encoding='utf-8')

    # ② 영인본 실물이 있어야 닫히는 편
    rows = []
    for s, r in sorted(audit.items()):
        v = r['verdict']
        reason = None
        if s in mapped and not mapped[s]['next_cnts']:
            reason = f'다음 글 지면을 NL에서 못 받음 ({why(mapped[s])[0]})'
            if v.startswith('지면결락'):
                # 둘 다 참일 수 있다 — 사이가 비었고, 그 다음 글도 못 받았다
                reason = f'🔴 {v} + ' + reason
        elif v.startswith('지면결락'):
            reason = f'{v} — 지면 자체가 없다'
        elif v == '계열바뀜':
            reason = '다음 항목의 쪽번호 계열이 다르다(諺文部 등) — 목차로는 잴 수 없다'
        elif v == '다음없음':
            reason = '그 호 목차의 마지막 항목이라 견줄 상대가 없다'
        elif v in ('목차없음', '목차에서못찾음', '다음쪽불명'):
            reason = f'{v} — 목차 쪽 문제'
        if not reason:
            continue
        rows.append({'series': s, 'tonggwon': r['tonggwon'], 'book': book_of(r['tonggwon']),
                     'publish': r['publish_date'][:7], 'title': r['title'],
                     'page_start': r['page_start'], 'last_held': r['last_held'],
                     'next_title': r['next_title'], 'next_page': r['next_page'],
                     'reason': reason})

    by_book = {}
    for r in rows:
        by_book.setdefault(r['book'], []).append(r)

    md = ['---', 'type: reference', 'created: 2026-08-12', 'updated: 2026-08-12',
          'tags: [천도교회월보, 영인본, 미해결]', '---', '',
          '# 영인본 실물을 봐야 닫히는 편', '',
          '『天道敎會月報 影印本』(天道敎中央總部, 1980) **26책**을 펴야 끝나는 일이다.',
          '디지털로는 더 갈 데가 없다 — 국립중앙도서관이 그 기사를 등재하지 않았거나,',
          '지면 자체가 없거나, 목차의 쪽번호 계열이 달라 잴 수가 없다.', '',
          '**책 번호를 붙여 둔다.** 「영인본을 보라」는 말은 26책 앞에서 쓸모가 없다.',
          '「제12책을 펴라」여야 사람이 움직인다. 통권 → 책은 목차집의',
          '`issues/<통권>.json`의 `source_book`에서 왔다.', '',
          '이 문서는 **파생물**이다. 고치지 말고 다시 생성한다.',
          '```bash', 'python3 scripts/06_magazines/build_pending_lists.py', '```', '',
          f'**{len(rows)}편 · 책 {len([b for b in by_book if b])}권**', '']
    for b in sorted(by_book, key=lambda x: (x is None, x)):
        lst = sorted(by_book[b], key=lambda r: (int(r['tonggwon']), r['series']))
        head = f'## 제{b}책' if b else '## 책 번호를 모름'
        tgs = sorted({int(r['tonggwon']) for r in lst})
        md += ['', f'{head} — 통권 {", ".join(str(t) for t in tgs)} · {len(lst)}편', '',
               '| 편 | 통권 | 발행 | 제목 | 쪽 | 보유 끝 | 봐야 할 자리 | 왜 |',
               '|---:|---:|---|---|---:|---:|---|---|']
        for r in lst:
            spot = (f"{r['next_page']}쪽 언저리" if r['next_page'] else '—')
            md.append(f"| {r['series']} | {r['tonggwon']} | {r['publish']} | {r['title'][:20]} | "
                      f"{r['page_start']} | {r['last_held'] or '—'} | {spot} | {r['reason']} |")
    md += ['', '## 보는 법', '',
           '📌 **끝 쪽은 다음 글 시작 쪽 −1이 아니다.** 한 지면에 앞 글의 꼬리와 다음 글의',
           '머리가 함께 앉는다. 그러니 **다음 글이 시작하는 쪽의 위쪽**을 본다. 거기 앞 글의',
           '꼬리가 있으면 우리 전사본이 짧은 것이고, 곧바로 제목이 오면 온전한 것이다.', '',
           '확인한 것은 [`bibliography_checks.csv`](bibliography_checks.csv)에 적는다 —',
           '이 코퍼스에서 **손으로 유지하는 유일한 파일**이다.']
    (REPO / 'pending_facsimile.md').write_text('\n'.join(md) + '\n', encoding='utf-8')

    print(f'pending_nl.md — NL에서 못 찾은 편 {len(missed)}')
    for k, v in sorted(tally.items(), key=lambda x: -x[1]):
        print(f'    {k:<12} {v}')
    print(f'pending_facsimile.md — 영인본 실물이 필요한 편 {len(rows)} · '
          f'책 {len([b for b in by_book if b])}권')
    for b in sorted(by_book, key=lambda x: (x is None, x)):
        print(f'    제{b or "?"}책  {len(by_book[b])}편')


if __name__ == '__main__':
    main()
