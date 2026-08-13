# -*- coding: utf-8 -*-
"""편별 대시보드 — 어느 편이 얼마나 무른지 한 표로.

86편이 다 같은 상태가 아니다. 정본이 아홉이고, 초벌 일흔여섯은 마커 수도 대분기 수도
제각각이며, Gemini가 통째로 빈 출력을 낸 구간이 편마다 다르다. **그 차이를 편마다
수치로 적어 두지 않으면 「미검수 코퍼스」라는 한 마디로 뭉뚱그려진다.**

열
    transcript          정본 · 초벌 · 없음
    markers             초벌본의 마커 수 (엔진이 갈린 자리)
    규칙·대장·C·G·미해소·면주   `wolbo_markers.py`의 등급별 자리 수
    auto_ratio          판단이 필요 없던 비율 = (규칙+대장)/markers
    big_diff_ratio      대분기(미해소) 비율 — 높을수록 근접독해가 필요하다
    gemini_empty_units  Gemini가 아무것도 뱉지 않은 단위 수 (그 구간의 「없음」은
                        「없다」가 아니라 「보지 않았다」다)
    claude_empty_units  같은 것을 Claude 쪽으로
    cross_checked       그 편에서 원본 지면과 대조를 마친 출현 자리 수
    keyword_hits        `keyword_index.csv`가 그 편에서 잡은 출현 수

쓰기
    python3 scripts/06_magazines/build_corpus_status.py
"""
import csv
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_keyword_index import VERIFIED_FULL  # noqa: E402
from build_reading import body_of  # noqa: E402
from wolbo_markers import GRADES, counts, load_ledger  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
WOLBO = ROOT / 'data' / '5_magazine_sources' / 'wolbo'

FIELDS = ['series', 'slug', 'publish_date', 'tonggwon', 'section', 'title', 'author',
          'page_in_journal', 'scan_pages', 'units', 'transcript', 'markers',
          '규칙', '대장', 'C', 'G', '미해소', '면주', '붕괴', 'auto_ratio', 'big_diff_ratio',
          'gemini_empty_units', 'claude_empty_units', 'cross_checked', 'keyword_hits',
          'reading_file']


def empty_units(adir, engine):
    d = adir / 'ocr' / engine
    if not d.is_dir():
        return ''
    n = 0
    for f in sorted(d.glob('unit_*.txt')):
        t = f.read_text(encoding='utf-8', errors='ignore')
        t = re.sub(r'^#.*$', '', t, flags=re.M)
        if not re.search(r'\[col\s*\d+\]\s*\S', t):
            n += 1
    return n


def main():
    ledger = load_ledger(WOLBO / 'marker_decisions.csv')
    with open(WOLBO / 'series_index.csv', encoding='utf-8-sig') as f:
        index = {int(r['series_index']): r for r in csv.DictReader(f)}

    kw_hits, kw_checked = Counter(), Counter()
    kpath = WOLBO / 'keyword_index.csv'
    if kpath.exists():
        with open(kpath, encoding='utf-8-sig') as f:
            for r in csv.DictReader(f):
                kw_hits[int(r['series'])] += 1
                if r['grade'] == '대조':
                    kw_checked[int(r['series'])] += 1
    else:
        print('⚠️ keyword_index.csv가 없다 — 먼저 build_keyword_index.py를 돌린다.',
              file=sys.stderr)

    dirs = {}
    for d in sorted((WOLBO / 'articles').iterdir()):
        m = re.match(r'(\d+)_', d.name)
        if d.is_dir() and m:
            dirs[int(m.group(1))] = d
    reading = {}
    for f in sorted((WOLBO / 'reading').glob('*.md')):
        m = re.match(r'(\d+)_', f.name)
        if m:
            reading[int(m.group(1))] = f.name

    rows = []
    for n, row in sorted(index.items()):
        adir = dirs.get(n)
        rec = dict(series=n, slug=adir.name if adir else '', publish_date=row['publish_date'],
                   tonggwon=row['tonggwon'], section=row['section'], title=row['title'],
                   author='', page_in_journal=row['page_in_journal'],
                   scan_pages=row['downloaded_pages'], units='', transcript='없음',
                   markers=0, auto_ratio='', big_diff_ratio='',
                   gemini_empty_units='', claude_empty_units='',
                   cross_checked=kw_checked[n], keyword_hits=kw_hits[n],
                   reading_file=reading.get(n, ''))
        rec.update({g: 0 for g in GRADES})

        if adir is not None:
            meta = yaml.safe_load((adir / 'meta.yaml').read_text(encoding='utf-8'))
            rec['author'] = (meta.get('article') or {}).get('author', '')
            rec['units'] = len(meta.get('units', []) or [])
            rec['scan_pages'] = len(meta.get('source_pages', []) or []) or rec['scan_pages']
            rec['gemini_empty_units'] = empty_units(adir, 'gemini')
            rec['claude_empty_units'] = empty_units(adir, 'claude_opus_4_7')
            if n in VERIFIED_FULL:
                rec['transcript'] = '정본'
            else:
                draft = next(iter(sorted((adir / 'transcripts').glob('*.draft_v0.md'))), None)
                if draft:
                    section = ((meta.get('ancillary') or {}).get('section_label')
                               or row['section'])
                    pagemap = {p.get('value'): p.get('hanja') for p in
                               ((meta.get('ancillary') or {}).get('page_numbers') or [])}
                    c = counts(body_of(draft.read_text(encoding='utf-8')),
                               section, pagemap, ledger)
                    rec['transcript'] = '초벌'
                    rec['markers'] = c['마커']
                    rec.update({g: c[g] for g in GRADES})
                    if c['마커']:
                        rec['auto_ratio'] = round(100 * (c['규칙'] + c['대장']) / c['마커'], 1)
                        rec['big_diff_ratio'] = round(100 * c['미해소'] / c['마커'], 1)
        rows.append(rec)

    out = WOLBO / 'CORPUS_STATUS.csv'
    with open(out, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    tot = Counter()
    for r in rows:
        tot['markers'] += r['markers']
        for g in GRADES:
            tot[g] += r[g]
        for k in ('gemini_empty_units', 'claude_empty_units', 'units'):
            tot[k] += r[k] or 0
    print(f'{out} — {len(rows)}편')
    print(f"정본 {sum(1 for r in rows if r['transcript'] == '정본')} · "
          f"초벌 {sum(1 for r in rows if r['transcript'] == '초벌')} · "
          f"없음 {sum(1 for r in rows if r['transcript'] == '없음')}")
    print(f"마커 {tot['markers']} · " + ' · '.join(f'{g} {tot[g]}' for g in GRADES))
    print(f"단위 {tot['units']} · Gemini 빈 단위 {tot['gemini_empty_units']} "
          f"({100 * tot['gemini_empty_units'] / tot['units']:.1f}%) · "
          f"Claude 빈 단위 {tot['claude_empty_units']} "
          f"({100 * tot['claude_empty_units'] / tot['units']:.1f}%)")
    worst = sorted((r for r in rows if r['transcript'] == '초벌'),
                   key=lambda r: -(r['big_diff_ratio'] or 0))[:8]
    print('\n대분기 비율이 높은 편 (근접독해 우선)')
    for r in worst:
        print(f"  C{r['series']:<3} {r['publish_date']} {r['title'][:22]:<24} "
              f"마커 {r['markers']:>4} · 미해소 {r['미해소']:>3} ({r['big_diff_ratio']}%)")


if __name__ == '__main__':
    main()
