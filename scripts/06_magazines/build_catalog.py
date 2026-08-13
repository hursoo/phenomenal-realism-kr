# -*- coding: utf-8 -*-
"""편별 대장 — 한 행이 한 편. **편의 모든 것이 여기서 보인다.**

왜
    2026-08-12 하루에 「我觀苦樂論」한 편의 상태를 적는 자리가 넷으로 흩어졌다 —
    제목은 `series_index.csv`에, 필자와 결락은 `meta.yaml`에, 사람이 확인한 사실은
    `verified_bibliography.md`에, 판독 상태는 `CORPUS_STATUS.csv`에. **한 편이 지금
    어떤 상태인지 알려면 넷을 열어야 했고, 하나를 고치면 나머지가 어긋난 채 남았다.**

    그래서 대장을 하나 세운다. 다만 **또 하나의 손 파일을 만들지는 않는다.**

    손으로 유지하는 것은 하나뿐 — `bibliography_checks.csv`. **사람이 지면을 열어야만
    알 수 있는 것**(제목·필자가 지면과 맞는가, 어디까지가 그 글인가)이 거기 들어간다.
    나머지는 전부 기계가 긁어 모은다.

무엇을 모으나
    series_index.csv        통권·발행·란·제목·쪽·CNTS
    편별 meta.yaml           필자·지면 수·단 수·구분선 검출 여부·결락(coverage)
    transcripts/            초벌인가 정본인가, 마커 몇 개인가
    ocr/<engine>/           엔진별로 몇 단을 읽었나, 빈 판독은 없나
    bibliography_checks.csv 사람이 확인한 서지 (유일한 손 파일)
    keyword_index.csv       그 편에서 원본과 대조를 마친 자리 수

쓰기
    python3 build_catalog.py                    # CATALOG.csv + CATALOG.md
    python3 build_catalog.py --md-only
"""
import argparse
import csv
import re
from pathlib import Path

import yaml
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_keyword_index import VERIFIED_FULL  # noqa: E402

WB = Path('/home/creta/work/0_tnt/hyeonsang/_ocr_experiments/cheondogyo_wolbo_series')
REPO = Path(__file__).resolve().parents[2] / 'data' / '5_magazine_sources' / 'wolbo'

FIELDS = ['series', 'slug', 'tonggwon', 'publish_date', 'section', 'title', 'author',
          'page_start', 'page_range', 'pages_held', 'partial', 'coverage_note',
          'bib_checked', 'bib_checker', 'bib_status', 'bib_note',
          'transcript', 'markers', 'big_diff', 'units', 'divider',
          'engines', 'empty_engines', 'cross_checked', 'keyword_hits']


def marker_stats(adir):
    td = adir / 'transcripts'
    fs = sorted(td.glob('*draft_v0.md')) if td.is_dir() else []
    if not fs:
        # 영인·단일 — 영인본 촬영을 한 엔진이 판독한 판. 마커가 없되 그것은
        # 「두 엔진이 같이 읽었다」가 아니라 「대조하지 않았다」는 뜻이다.
        if td.is_dir() and any(td.glob('*.영인단일.md')):
            return '영인·단일', '', ''
        return '', '', ''
    t = fs[0].read_text(encoding='utf-8', errors='ignore')
    i = t.find('[body]')
    t = t[i:] if i >= 0 else t
    ms = re.findall(r'⚠️\[C:(.*?)\|G:(.*?)(?:\|P:[^\]]*)?\]', t)
    big = sum(1 for c, g in ms if max(len(c), len(g)) >= 15)
    return 'draft', len(ms), big


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--md-only', action='store_true')
    args = ap.parse_args()

    with open(WB / 'series_index.csv', encoding='utf-8-sig') as f:
        index = list(csv.DictReader(f))

    checks = {}
    cp = REPO / 'bibliography_checks.csv'
    if cp.exists():
        with open(cp, encoding='utf-8-sig') as f:
            for r in csv.DictReader(f):
                if r.get('series'):
                    checks[int(r['series'])] = r

    kw, cross = {}, {}
    kp = REPO / 'keyword_index.csv'
    if kp.exists():
        with open(kp, encoding='utf-8-sig') as f:
            for r in csv.DictReader(f):
                s = int(r['series'])
                kw[s] = kw.get(s, 0) + 1
                if r['grade'] == '대조':
                    cross[s] = cross.get(s, 0) + 1

    dirs = {}
    for d in sorted((WB / 'articles').iterdir()):
        m = re.match(r'(\d+)_', d.name)
        if d.is_dir() and m:
            dirs[int(m.group(1))] = d

    rows = []
    for r in index:
        n = int(r['series_index'])
        d = dirs.get(n)
        rec = dict.fromkeys(FIELDS, '')
        rec.update(series=n, tonggwon=r['tonggwon'], publish_date=r['publish_date'],
                   section=r['section'], title=r['title'],
                   page_start=r['page_in_journal'], partial=r.get('partial', ''),
                   pages_held=r.get('downloaded_pages', ''),
                   keyword_hits=kw.get(n, 0), cross_checked=cross.get(n, 0))
        if d:
            rec['slug'] = d.name
            mp = d / 'meta.yaml'
            if mp.exists():
                meta = yaml.safe_load(mp.read_text(encoding='utf-8'))
                rec['author'] = (meta.get('article') or {}).get('author', '')
                rec['units'] = len(meta.get('units') or [])
                det = [u.get('divider_detected') for u in (meta.get('units') or [])]
                rec['divider'] = '검출' if any(det) else '고정값'
                cov = meta.get('coverage') or {}
                if cov:
                    rec['page_range'] = cov.get('실제_범위', '')
                    rec['coverage_note'] = f"보유 {cov.get('보유','')} · 결락 {cov.get('결락','')}"
            st, mk, big = marker_stats(d)
            rec['transcript'], rec['markers'], rec['big_diff'] = st, mk, big
            # 정본은 두 곳에 산다 — articles/ 안(C01)과 verified_transcripts/(C30~C37)
            if n in VERIFIED_FULL or ((d / 'transcripts').is_dir() and any(
                    f.name.endswith('.high_fidelity.md') for f in (d / 'transcripts').iterdir())):
                rec['transcript'] = '정본'
            engs, empty = [], []
            if (d / 'ocr').is_dir():
                for e in sorted((d / 'ocr').iterdir()):
                    if not e.is_dir() or e.name in ('gpt5', 'paddle'):
                        continue
                    fs = list(e.glob('*.txt'))
                    if fs:
                        engs.append(f'{e.name}:{len(fs)}')
                        if sum(1 for f in fs if not re.search(
                                r'\[col\s*\d+\]\s*\S', f.read_text(encoding='utf-8', errors='ignore'))):
                            empty.append(e.name)
            rec['engines'] = ' '.join(engs)
            rec['empty_engines'] = ','.join(empty)
        c = checks.get(n)
        if c:
            rec.update(bib_checked=c['checked'], bib_checker=c['checker'],
                       bib_status=c['status'], bib_note=c['note'][:160])
            # 사람이 지면에서 읽은 필자가 있으면 **그것이 이긴다**
            if c.get('author_verified'):
                rec['author'] = c['author_verified']
            if c.get('title_verified'):
                rec['title'] = c['title_verified']
            if c.get('page_range'):
                rec['page_range'] = rec['page_range'] or c['page_range']
        rows.append(rec)

    out = REPO / 'CATALOG.csv'
    if not args.md_only:
        with open(out, 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader(); w.writerows(rows)

    # 사람이 보는 판
    checked = [r for r in rows if r['bib_status']]
    # 편 번호가 없는 확인(편외 등)도 빠뜨리지 않는다
    loose = [c for k, c in checks.items() if False] + [
        c for c in (list(csv.DictReader(open(cp, encoding='utf-8-sig'))) if cp.exists() else [])
        if not c.get('series')]
    nodraft = [r for r in rows if not r['transcript']]
    md = ['---', 'type: reference', 'created: 2026-08-12',
          'updated: 2026-08-12', 'tags: [천도교회월보, 대장]', '---', '',
          '# 편별 대장', '',
          '한 행이 한 편이다. **이 편이 지금 어떤 상태인가**를 여기서 본다 — 서지가',
          '지면과 맞는지 사람이 확인했는가, 판독은 어디까지 왔는가, 지면은 다 있는가.', '',
          '이 문서는 **파생물**이다. 고치지 말고 다시 생성한다.',
          '```bash', 'python3 scripts/06_magazines/build_catalog.py', '```', '',
          '손으로 유지하는 것은 [`bibliography_checks.csv`](bibliography_checks.csv) 하나뿐이다 —',
          '**사람이 지면을 열어야만 알 수 있는 것**이 거기 들어간다. 나머지 열은 기계가 모은다.', '',
          f'**{len(rows)}편** · 서지 확인 {len(checked)} · 전사본 없음 {len(nodraft)}', '',
          '## 사람이 지면을 열어 확인한 편', '',
          '| 편 | 통권 | 제목 | 필자 | 쪽 | 확인 | 상태 | 비고 |',
          '|---:|---:|---|---|---|---|---|---|']
    for r in checked:
        md.append(f"| {r['series']} | {r['tonggwon']} | {r['title']} | {r['author'] or '—'} | "
                  f"{r['page_range'] or r['page_start']} | {r['bib_checked']} | "
                  f"**{r['bib_status']}** | {r['bib_note'][:70]} |")
    if loose:
        md += ['', '### 편 번호가 없는 확인 (편외 등)', '',
               '| 제목 | 필자 | 쪽 | 확인 | 상태 | 비고 |', '|---|---|---|---|---|---|']
        for c in loose:
            md.append(f"| {c['title_verified']} | {c['author_verified']} | {c['page_range']} | "
                      f"{c['checked']} | **{c['status']}** | {c['note'][:70]} |")
    md += ['', '## 전체', '',
           '| 편 | 통권 | 발행 | 제목 | 필자 | 전사 | 마커 | 대분기 | 단 | 구분선 | 대조 | 서지확인 |',
           '|---:|---:|---|---|---|---|---:|---:|---:|---|---:|---|']
    for r in rows:
        md.append(f"| {r['series']} | {r['tonggwon']} | {r['publish_date'][:7]} | "
                  f"{r['title'][:22]} | {r['author'] or '—'} | {r['transcript'] or '—'} | "
                  f"{r['markers']} | {r['big_diff']} | {r['units']} | {r['divider'] or '—'} | "
                  f"{r['cross_checked'] or ''} | {r['bib_status'] or ''} |")
    (REPO / 'CATALOG.md').write_text('\n'.join(md) + '\n', encoding='utf-8')

    print(f'{out} · CATALOG.md — {len(rows)}편')
    print(f'  서지 확인 {len(checked)}(+편외 {len(loose)}) · 전사본 없음 {len(nodraft)} · '
          f'정본 {sum(1 for r in rows if r["transcript"] == "정본")}')
    if nodraft:
        print('  전사본 없는 편: ' + ', '.join(f"#{r['series']}" for r in nodraft[:20])
              + (' …' if len(nodraft) > 20 else ''))


if __name__ == '__main__':
    main()
