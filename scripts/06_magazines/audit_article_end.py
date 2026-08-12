# -*- coding: utf-8 -*-
"""**이 편의 끝이 정말 끝인가** — 목차의 다음 글 시작 쪽으로 158편을 한꺼번에 재기.

왜
    2026-08-12에 정본 아홉 편을 재어 보니 **둘이 끊겨 있었다.** C34는 「符」 한 자에서,
    C36은 「大」 한 자에서 멈춰 있었고, 둘 다 **쪽바꿈이 낱말을 가른 자리**였다.
    사람이 본문을 아무리 들여다봐도 보이지 않는다 — 다음 지면을 열어야 보인다.

    아홉 편에서 둘이면 158편에서는 더 나온다. 다만 158편을 다 열어 볼 수는 없으므로
    **먼저 기계로 추린다.**

무엇으로 재나
    두 수를 견준다.

        마지막 보유 쪽 = 목차의 이 글 시작 쪽 + 내려받은 지면 수 − 1
        다음 글 시작 쪽 = 같은 호 목차에서 이 글 바로 다음 항목의 쪽

    📌 **목차의 「다음 글 시작 쪽」은 앞 글의 끝 쪽이 아니다.** 한 지면에 앞 글의 꼬리와
    다음 글의 머리가 함께 앉기 때문이다. 그래서 판정은 이렇다.

        마지막 보유 == 다음 글 시작    ✅ **자력확인가능.** 다음 글이 우리 마지막 지면에서
                                        시작하므로 그 지면에 앞 글의 끝이 함께 있다.
                                        받을 것 없이 우리 손의 이미지로 끝난다
                                        (C01·C30·C33·C35·C37이 이 경우였다)
        마지막 보유 == 다음 글 시작 −1  ❓ **다음지면필요.** 여기서 두 갈래가 갈린다 —
                                        글이 마지막 지면 밑까지 채우고 끝났거나,
                                        꼬리가 다음 쪽으로 넘어갔거나. **우리 지면만으로는
                                        가릴 수 없다.** C34·C36이 이 자리에서 끊겨 있었다
        마지막 보유 <  다음 글 시작 −1  🔴 **지면결락.** 사이가 통째로 빈다 (我觀苦樂論)
        마지막 보유 >  다음 글 시작     ⚠️ 목차가 밀렸거나 우리 쪽 수가 틀렸다

    ❓를 🔴로 읽지 않는다. **「끊겼다」가 아니라 「모른다」다.** 아는 방법은 하나뿐이니
    다음 글의 첫 지면을 받아 그 위를 보는 것이다.

한계 — 이것은 **선별기이지 판정기가 아니다**
    ① 목차 자체가 밀린 자리가 있다(통93에서 두 번). 목차를 자로 쓰는 이상 자가 휜다.
    ② 諺文部처럼 **란마다 쪽번호를 새로 매기는** 구간이 있다. 다음 항목의 쪽이 이 글의
       쪽보다 작으면 번호 계열이 바뀐 것이므로 `계열바뀜`으로 빼 둔다.
    ③ 마지막 항목(그 호의 끝)은 견줄 상대가 없어 `다음없음`이다.
    걸린 편은 **사람이 지면을 열어** 확인하고 `bibliography_checks.csv`에 적는다.

쓰기
    python3 audit_article_end.py                 # 요약 + article_end_audit.md/.csv
    python3 audit_article_end.py --only 모자람
"""
import argparse
import csv
import re
from pathlib import Path

WB = Path('/home/creta/work/0_tnt/hyeonsang/_ocr_experiments/cheondogyo_wolbo_series')
REPO = Path(__file__).resolve().parents[2] / 'data' / '5_magazine_sources' / 'wolbo'
MOKLOK = Path('/mnt/e/#DT_DATA_all/0_srh/magazine/cheondo-weolbo/raw/moklok_facs/articles.tsv')

FIELDS = ['series', 'tonggwon', 'publish_date', 'section', 'title', 'page_start',
          'pages_held', 'last_held', 'next_title', 'next_page', 'gap', 'verdict']


def to_int(s):
    m = re.search(r'\d+', str(s or ''))
    return int(m.group()) if m else None


def load_moklok():
    """호마다 목차를 실린 차례대로 들고 있는다. 차례 자체가 정보다."""
    by_issue = {}
    if not MOKLOK.exists():
        return by_issue
    with MOKLOK.open(encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            tg = to_int(r.get('tonggwon'))
            if tg is None:
                continue
            by_issue.setdefault(tg, []).append(
                {'section': (r.get('section') or '').strip(),
                 'title': (r.get('title') or '').strip(),
                 'author': (r.get('author') or '').strip(),
                 'page': to_int(r.get('page'))})
    return by_issue


def norm(s):
    return re.sub(r'[\s·()（）\[\]「」]', '', s or '')


def find_row(entries, section, page, title):
    """목차에서 이 글의 자리를 찾는다. 쪽이 먼저고 제목은 거드는 역할이다."""
    cands = [i for i, e in enumerate(entries) if e['page'] == page]
    if not cands:
        return None
    if len(cands) == 1:
        return cands[0]
    for i in cands:                                   # 같은 쪽이 여럿이면 란으로
        if entries[i]['section'] == section:
            return i
    for i in cands:                                   # 그래도 여럿이면 제목으로
        if norm(entries[i]['title'])[:6] == norm(title)[:6]:
            return i
    return cands[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='')
    args = ap.parse_args()

    by_issue = load_moklok()
    if not by_issue:
        raise SystemExit(f'목차를 못 읽었다: {MOKLOK}\n'
                         '외장 드라이브가 붙어 있는지 본다.')

    with open(WB / 'series_index.csv', encoding='utf-8-sig') as f:
        index = list(csv.DictReader(f))

    rows = []
    for r in index:
        n = to_int(r['series_index'])
        tg = to_int(r['tonggwon'])
        start = to_int(r['page_in_journal'])
        held = to_int(r['downloaded_pages']) or 0
        rec = dict.fromkeys(FIELDS, '')
        rec.update(series=n, tonggwon=tg, publish_date=r['publish_date'],
                   section=r['section'], title=r['title'],
                   page_start=start, pages_held=held)

        entries = by_issue.get(tg)
        if not held:
            rec['verdict'] = '지면없음'
        elif not entries or start is None:
            rec['verdict'] = '목차없음'
        else:
            i = find_row(entries, r['section'], start, r['title'])
            if i is None:
                rec['verdict'] = '목차에서못찾음'
            elif i + 1 >= len(entries):
                rec['verdict'] = '다음없음'
            else:
                nxt = entries[i + 1]
                last = start + held - 1
                rec.update(last_held=last, next_title=nxt['title'], next_page=nxt['page'])
                if nxt['page'] is None:
                    rec['verdict'] = '다음쪽불명'
                elif nxt['page'] < start:
                    rec['verdict'] = '계열바뀜'      # 란이 바뀌며 쪽번호가 새로 시작
                else:
                    gap = nxt['page'] - last
                    rec['gap'] = gap
                    rec['verdict'] = ('자력확인가능' if gap == 0 else
                                      '다음지면필요' if gap == 1 else
                                      f'지면결락{gap - 1}면' if gap > 1 else '초과')
        rows.append(rec)

    with open(REPO / 'article_end_audit.csv', 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader(); w.writerows(rows)

    order = ['지면결락', '초과', '다음지면필요', '자력확인가능', '계열바뀜', '다음없음',
             '지면없음', '목차없음', '목차에서못찾음', '다음쪽불명']
    def key(v):
        for i, o in enumerate(order):
            if str(v).startswith(o):
                return i
        return len(order)
    tally = {}
    for r in rows:
        tally[r['verdict']] = tally.get(r['verdict'], 0) + 1

    susp = sorted([r for r in rows
                   if str(r['verdict']).startswith(('지면결락', '초과', '다음지면필요'))],
                  key=lambda r: (key(r['verdict']), r['series']))

    md = ['---', 'type: reference', 'created: 2026-08-12', 'updated: 2026-08-12',
          'tags: [천도교회월보, 감사, 완결성]', '---', '',
          '# 이 편의 끝이 정말 끝인가 — 158편 일괄 재기', '',
          '정본 아홉 편을 재어 보니 **둘이 끊겨 있었다**(C34·C36). 둘 다 쪽바꿈이 낱말을',
          '가른 자리였고, 본문만 봐서는 보이지 않았다. 아홉에서 둘이면 158편에서는 더 나온다.',
          '그래서 **목차의 다음 글 시작 쪽**을 자로 삼아 한꺼번에 쟀다.', '',
          '이 문서는 **파생물**이다. 고치지 말고 다시 생성한다.',
          '```bash', 'python3 scripts/06_magazines/audit_article_end.py', '```', '',
          '📌 **목차의 「다음 글 시작 쪽」은 앞 글의 끝 쪽이 아니다.** 한 지면에 앞 글의',
          '꼬리와 다음 글의 머리가 함께 앉는다. 그래서 **「마지막 보유 = 다음 글 시작」이',
          '오히려 좋은 소식**이다 — 그 지면에 끝이 함께 찍혀 있으므로 받을 것이 없다.',
          '한 면 모자란 쪽이 **모르는** 자리다.', '',
          '## 판정 집계', '', '| 판정 | 편수 | 뜻 |', '|---|---:|---|']
    MEAN = {'자력확인가능': '✅ 다음 글이 우리 마지막 지면에서 시작한다 — 받을 것 없이 그 이미지로 끝난다',
            '다음지면필요': '❓ **모른다.** 마지막 지면에서 끝났을 수도, 꼬리가 넘어갔을 수도 있다. C34·C36이 이 자리에서 끊겨 있었다',
            '초과': '⚠️ 목차가 밀렸거나 우리 쪽 수가 틀렸다',
            '계열바뀜': '다음 항목의 쪽이 더 작다 — 란이 바뀌며 쪽번호가 새로 시작(諺文部 등)',
            '다음없음': '그 호 목차의 마지막 항목이라 견줄 상대가 없다',
            '지면없음': '아직 내려받지 않았다',
            '목차없음': '그 호가 목차집에 없다',
            '목차에서못찾음': '쪽으로 자리를 못 찾았다',
            '다음쪽불명': '다음 항목에 쪽이 안 적혀 있다'}
    for v in sorted(tally, key=key):
        d = MEAN.get(v, '🔴 사이가 통째로 빈다 — 지면 자체가 모자란다' if str(v).startswith('지면결락') else '')
        md.append(f'| {v} | {tally[v]} | {d} |')

    md += ['', '## 아직 끝을 모르는 편', '',
           f'**{len(susp)}편.** 여기 오른 편은 **「끊겼다」가 아니라 「끊겼는지 모른다」**다.',
           '아는 방법은 하나뿐이니 다음 글의 첫 지면을 받아 그 위를 보는 것이다.',
           '확인하고 나면 [`bibliography_checks.csv`](bibliography_checks.csv)에 적는다.', '',
           '| 편 | 통권 | 발행 | 란 | 제목 | 시작 | 보유 | 마지막 | 다음 글 | 다음 쪽 | 판정 |',
           '|---:|---:|---|---|---|---:|---:|---:|---|---:|---|']
    for r in susp:
        md.append(f"| {r['series']} | {r['tonggwon']} | {r['publish_date'][:7]} | {r['section']} | "
                  f"{str(r['title'])[:20]} | {r['page_start']} | {r['pages_held']} | {r['last_held']} | "
                  f"{str(r['next_title'])[:18]} | {r['next_page']} | **{r['verdict']}** |")
    md += ['', '## 이 자의 한계', '',
           '- 목차 자체가 밀린 자리가 있다(통93에서 두 번). **자를 목차로 삼는 이상 자가 휜다.**',
           '- 諺文部처럼 란마다 쪽번호를 새로 매기는 구간은 `계열바뀜`으로 빼 두었다 —',
           '  **빠뜨린 것이 아니라 이 자로는 못 재는 것**이다.',
           '- 그 호의 마지막 항목은 견줄 상대가 없다(`다음없음`).',
           '- 그러므로 이것은 **선별기이지 판정기가 아니다.** 최종 권위는 지면이다.']
    (REPO / 'article_end_audit.md').write_text('\n'.join(md) + '\n', encoding='utf-8')

    print(f'{len(rows)}편')
    for v in sorted(tally, key=key):
        print(f'  {v:<14} {tally[v]:>4}')
    print(f'\n지면을 열어 봐야 할 편 {len(susp)}')
    for r in susp[:25]:
        print(f"  #{r['series']:<4} 통{r['tonggwon']:<4} {str(r['title'])[:16]:<18} "
              f"{r['page_start']}+{r['pages_held']}→{r['last_held']} / 다음 {r['next_page']} "
              f"({r['next_title'][:14]})  {r['verdict']}")
    if len(susp) > 25:
        print(f'  … 그 밖 {len(susp) - 25}편')


if __name__ == '__main__':
    main()
