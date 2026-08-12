# -*- coding: utf-8 -*-
"""원본 지면 폴더 감사 — 100폴더가 무엇인지 하나도 남기지 않고 가른다.

`source_pages/`에는 폴더가 100개인데 코퍼스는 86편이다. **열넷이 무엇인지 아무 데도
적혀 있지 않았다.** 2026-08-12에 셋을 갈라 이름을 고쳤다 — 편 폴더는 전사 작업 폴더와
같은 `NN_슬러그_YYYY-MM`으로, 나머지는 `_중복/`·`_편외/`로.

이 스크립트는 폴더마다 넷 중 하나로 판정한다.

    편        series_index의 한 편에 대응한다
    중복      다른 폴더와 지면 이미지가 **바이트 단위로 같다**(같은 글의 두 레코드)
    별판      같은 글의 **다른 스캔**(NL 레코드가 둘이고 이미지가 다르다)
    편외      코퍼스에 없는 글 — 신원을 지면에서 직접 확인해야 한다

판정은 sha256으로 한다. 제목·날짜 메타는 NL 서지가 틀린 경우가 있어 근거로 쓰지 않는다
(실제로 「夢天解」의 필자는 NL 서지가 李敦化라 적었으나 지면에는 李敦性이다).

쓰기
    python3 scripts/06_magazines/audit_source_pages.py
"""
import csv
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WOLBO = ROOT / 'data' / '5_magazine_sources' / 'wolbo'
SP = WOLBO / 'source_pages'

# 편외·별판으로 판정된 폴더의 신원. **지면 이미지를 직접 읽어 확인한 것만 적는다.**
# NL 서지의 제목·필자·발행일은 근거로 쓰지 않는다(틀린 사례가 있다).
IDENTIFIED = {
    '_편외/편외_我觀苦樂論_1913-07': dict(
        cnts='CNTS-00048064195', 판정='편외', 제목='我觀苦樂論', 필자='李敦化', 게재='講演', 쪽='19',
        추정호='통권 36 (1913-07-15)',
        확인='지면 제목·란·쪽수를 직접 확인. 총목록의 1913-07-15 통36 講演 19쪽과 일치',
        메모='코퍼스에 없는 이돈화 글. 지면이 이미 있으므로 전사하면 편입할 수 있다'),
    '_편외/편외_偉大한心의世界_1918-04': dict(
        cnts='CNTS-00048037679', 판정='편외', 제목='偉大ᄒᆞᆫ 心의 世界', 필자='李敦化', 게재='敎理部', 쪽='16',
        추정호='제93호 (1918-04-15)',
        확인='지면 제목·필자·란·쪽수를 직접 확인',
        메모='코퍼스에 없는 이돈화 글. 총목록은 통93 敎理部에 「神平河善論」을 올려 두어 '
             '목록과 지면이 어긋난다 — 같은 호에 둘이 실렸는지 확인이 필요하다'),
    '_편외/편외_夢天解_1912-01_李敎性': dict(
        cnts='CNTS-00048047578', 판정='편외', 제목='夢天解', 필자='李敎性', 게재='雜俎', 쪽='41',
        추정호='통권 18 (1912-01-15)',
        확인='지면의 필자를 4배로 확대해 읽었다 — **李敎性**. 영인본 목차(통18 雜俎 41쪽)도 '
             '李敎性으로 적어 두 증인이 일치한다',
        메모='🔴 NL 서지는 필자를 李敦化로 적었다 — 서지 오류다. **이돈화의 글이 아니다.** '
             '⚠️ 2026-08-12 첫 판독에서는 李敦性으로 읽었으나 확대해 보니 敦이 아니라 敎였다. '
             '단(段) 배율로는 敦/敎가 갈리지 않는다는 것을 필자명에서 실증한 사례'),
    '_편외/별판_進化의側面으로본人乃天_1922-02': dict(
        cnts='CNTS-00048079265', 판정='별판', 제목='進化의 側面으로 본 人乃天', 필자='李敦化', 게재='', 쪽='8',
        추정호='통권 138 (1922-02-15)',
        확인='지면 제목·필자·쪽수를 직접 확인 — C72와 같은 글',
        메모='C72(`CNTS-00133846655`)와 같은 글의 다른 스캔. NL에 레코드가 둘이다'),
}


def sig(d):
    return tuple(sorted(hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in sorted(d.glob('*.jpg'))))


def main():
    with open(WOLBO / 'series_index.csv', encoding='utf-8-sig') as f:
        index = list(csv.DictReader(f))
    by_cnts = {r['cnts_id']: r for r in index if r['cnts_id']}
    by_series = {int(r['series_index']): r for r in index}

    dirs = sorted([d for d in SP.iterdir() if d.is_dir() and not d.name.startswith('_')]
                  + [d for sub in ('_중복', '_편외') if (SP / sub).is_dir()
                     for d in sorted((SP / sub).iterdir()) if d.is_dir()])
    rel = {d: str(d.relative_to(SP)) for d in dirs}
    sigs = {rel[d]: sig(d) for d in dirs}
    same = {}
    for name, s in sigs.items():
        same.setdefault(s, []).append(name)

    rows = []
    for d in dirs:
        n = rel[d]
        pages = len(sigs[n])
        series, note = '', ''
        m = re.match(r'(\d+)_', n)
        if m and int(m.group(1)) in by_series:
            series, verdict = int(m.group(1)), '편'
        elif n in by_cnts:
            series, verdict = int(by_cnts[n]['series_index']), '편'
        elif n.startswith('_중복/'):
            twin = [x for x in same[sigs[n]] if x != n]
            verdict, note = '중복', ('지면이 바이트 단위로 같다 → ' + ', '.join(twin)
                                   if twin else '⚠️ 짝을 찾지 못했다')
            mm = re.match(r'(\d+)_', twin[0]) if twin else None
            series = int(mm.group(1)) if mm else ''
        else:
            twin = [x for x in same[sigs[n]] if x != n]
            if twin:
                verdict, note = '중복', '지면이 바이트 단위로 같다 → ' + ', '.join(twin)
                mm = re.match(r'(\d+)_', twin[0])
                series = int(mm.group(1)) if mm else ''
            else:
                verdict = IDENTIFIED.get(n, {}).get('판정', '')
                if not verdict:
                    verdict = '별판' if n.startswith('_편외/별판') else (
                        '편외' if n.startswith('_편외/') else '미확인')
        ident = IDENTIFIED.get(n, {})
        title = ident.get('제목') or (by_series[series]['title'] if series else '')
        rows.append(dict(
            folder=n, verdict=verdict, series=series, pages=pages,
            title=title, author=ident.get('필자', ''), cnts=ident.get('cnts', ''),
            issue=ident.get('추정호', ''),
            note=note or ident.get('메모', ''),
        ))

    out = WOLBO / 'source_pages_MAP.csv'
    with open(out, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['folder', 'verdict', 'series', 'pages',
                                          'title', 'author', 'cnts', 'issue', 'note'])
        w.writeheader()
        w.writerows(rows)

    tally = {}
    for r in rows:
        tally[r['verdict']] = tally.get(r['verdict'], 0) + 1
    print(f'{out} — 폴더 {len(rows)} · 지면 {sum(r["pages"] for r in rows)}장')
    print(' · '.join(f'{k} {v}' for k, v in sorted(tally.items())))
    covered = {r['series'] for r in rows if r['verdict'] == '편'}
    missing = sorted(set(by_series) - covered)
    print(f'지면이 있는 편 {len(covered)}/86' + (f' · 없는 편 {missing}' if missing else ''))
    for r in rows:
        if r['verdict'] in ('편외', '별판', '미확인'):
            print(f'  [{r["verdict"]}] {r["folder"]} {r["pages"]}면 '
                  f'{r["title"]} {r["author"]} {r["issue"]}')


if __name__ == '__main__':
    main()
