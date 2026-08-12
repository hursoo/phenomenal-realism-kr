# -*- coding: utf-8 -*-
"""**다음 글의 첫 지면을 받아 온다** — 앞 글의 끝을 그 위에서 읽기 위해.

왜
    `audit_article_end.py`가 81편을 「다음지면필요」로 남겼다. 그 자리에서 두 갈래가
    갈린다 — 글이 마지막 지면 밑까지 채우고 끝났거나, 꼬리가 다음 쪽으로 넘어갔거나.
    **우리 지면만으로는 가릴 수 없다.**

    싸게 가리려고 하단 왼쪽의 여백을 재 봤으나(`detect_tail_blank.py`) 졌다. 월보는
    한 지면의 상단과 하단에 **서로 다른 글**을 앉히므로 하단의 여백은 이 글의 끝과
    상관이 없다. C34·C36이 둘 다 「끝남」으로 잘못 나왔다.

    그러니 확실한 길로 간다 — **다음 글의 첫 지면을 받는다.** 거기 위쪽에 앞 글의
    꼬리가 앉아 있으면 우리 전사본이 짧은 것이고, 곧바로 제목이 오면 온전한 것이다.

무엇을 하나
    ① 목차에서 얻은 **다음 글 제목**에서 띄어쓰기를 지우고 국립중앙도서관을 검색한다
       (NL의 기사 제목에는 공백이 없다. 공백을 넣으면 못 찾는다)
    ② **호수**가 맞는 CNTS 레코드를 고른다. 목록에 「[天道敎會月報 第六十三號]」가 함께
       찍히므로 통권을 한자 수로 바꿔 맞춘다.
       🔴 **발행일로 거르면 안 된다** — NL은 통63(1915-10-15)을 `19150115`로 적어 두었다.
       호가 아니라 그 해 첫 호의 날짜를 넣은 듯하다. 날짜 필드를 믿을 수 없다
    ③ 그 레코드의 지면을 내려받는다 (`scrape_nl_articles`가 편 단위로 받는다)
    ④ 편 번호 ↔ 다음 글 CNTS 대응을 `next_article_map.csv`에 적는다

    받은 지면은 **우리 코퍼스의 편이 아니다.** 앞 글의 끝을 확인하는 근거일 뿐이므로
    `series_index.csv`에 넣지 않는다. raw에는 다른 편과 같은 자리에 앉는다 —
    CNTS 번호가 그 신원이기 때문이다.

한계
    - NL은 **기사 단위로 등재하며 어떤 기사는 아예 없다.** 오늘 「李一得氏」가 0건이었다.
      못 찾은 것은 `못찾음`으로 남고, 그 편의 끝은 영인본 실물을 봐야 한다.
    - 제목이 목차 OCR을 거친 것이라 글자가 틀어져 있을 수 있다. 그래서 검색은
      **제목 앞머리**로 하고 발행일로 거른다.

쓰기
    python3 fetch_next_article_pages.py --dry-run       # 무엇을 찾았는지만
    python3 fetch_next_article_pages.py --apply
    python3 fetch_next_article_pages.py --apply --series 34,36
"""
import argparse
import csv
import html
import re
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

RAW = Path('/home/creta/work/0_tnt/hyeonsang/raw/journals/cheondogyo_wolbo/nl_bibliography')
SCRAPER = Path('/mnt/e/#DT_DATA_all/0_srh/magazine/cheondo-weolbo/scraper')
REPO = Path(__file__).resolve().parents[2] / 'data' / '5_magazine_sources' / 'wolbo'

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120 Safari/537.36')
SEARCH = 'https://www.nl.go.kr/NL/contents/search.do?'


def strip_tags(s):
    return re.sub(r'<[^>]+>', '', html.unescape(s)).strip()


def nl_search(kwd, pause=1.0):
    """제목으로 찾는다. {CNTS: 목록에 찍힌 제목} 을 돌려준다.

    목록의 제목은 「[天道敎會月報 第六十三號] 講演 : 片時後寂寞을斷不爲라」 꼴이라
    호수와 란이 함께 들어 있다. 그것이 거르는 자다.
    """
    q = urllib.parse.urlencode({'pageSize': '50', 'hanjaFlag': 'N', 'kwd': kwd})
    r = subprocess.run(['curl', '-s', '-m', '40', '-A', UA, SEARCH + q],
                       capture_output=True, text=True)
    time.sleep(pause)                       # 남의 서버다. 몰아치지 않는다
    out = {}
    for k, t in re.findall(r'viewKey=([A-Za-z0-9\-]+)[^>]*>(.*?)</a>', r.stdout, re.S):
        if k.startswith('CNTS'):
            t = strip_tags(t)
            if t and k not in out:
                out[k] = t
    return out, r.stdout


def norm(s):
    return re.sub(r'[\s·,.()（）\[\]「」『』]', '', s or '')


HANJA_NUM = '零一二三四五六七八九'


def hanja_ho(n):
    """126 → 「第百二十六號」. 목록에 찍히는 호수 표기를 만든다."""
    n = int(n)
    if n <= 0:
        return ''
    out = ''
    if n >= 100:
        h = n // 100
        out += ('' if h == 1 else HANJA_NUM[h]) + '百'
        n %= 100
    if n >= 10:
        t_ = n // 10
        out += ('' if t_ == 1 else HANJA_NUM[t_]) + '十'
        n %= 10
    if n:
        out += HANJA_NUM[n]
    return '第' + out + '號'


def pick(hits, title, tonggwon):
    """**호수**가 맞는 것을 고른다. 제목만으로는 연재·동명이 섞인다."""
    ho = hanja_ho(tonggwon)
    cands = []
    for k, t in hits.items():
        score = 0
        if ho and ho in t:                      # 「[天道敎會月報 第六十三號] 講演 : …」
            score += 10
        if '天道敎會月報' in t or '천도교회월보' in t:
            score += 3
        body = t.split(':', 1)[-1]              # 「란 : 제목」에서 제목만
        n1, n2 = norm(body), norm(title)
        if n1 == n2:
            score += 5
        elif n1.startswith(n2[:4]) or n2.startswith(n1[:4]):
            score += 2
        cands.append((score, k, t))
    cands.sort(reverse=True)
    if not cands:
        return None, None, '못찾음'
    top = cands[0]
    if top[0] >= 13:
        return top[1], top[2], '호수일치'
    if top[0] >= 10:
        return top[1], top[2], '⚠️호수만일치'
    if top[0] >= 5:
        return top[1], top[2], '⚠️제목만일치'
    return None, None, '못찾음'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--series', default='')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--pause', type=float, default=1.0)
    args = ap.parse_args()
    apply_ = args.apply and not args.dry_run

    src = REPO / 'article_end_audit.csv'
    if not src.exists():
        raise SystemExit('먼저 audit_article_end.py 를 돌린다')
    rows = list(csv.DictReader(src.open(encoding='utf-8-sig')))
    want = set(int(s) for s in args.series.split(',')) if args.series else None
    todo = [r for r in rows
            if (r['verdict'] == '다음지면필요' or r['verdict'].startswith('지면결락'))
            and r['next_title']
            and (want is None or int(r['series']) in want)]

    # 이미 받아 둔 것은 다시 받지 않는다
    prev = {}
    mp = REPO / 'next_article_map.csv'
    if mp.exists():
        for r in csv.DictReader(mp.open(encoding='utf-8-sig')):
            prev[int(r['series'])] = r

    art = None
    if apply_:
        sys.path.insert(0, str(SCRAPER))
        import scrape_nl_articles as art   # noqa: PLC0415
        art.ARTICLES_DIR = RAW / 'articles'
        art.LOG_DIR = RAW / 'logs'
        art.ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
        art.LOG_DIR.mkdir(parents=True, exist_ok=True)
        sess = art.make_session()

    out, found, missed = [], 0, 0
    print(f'대상 {len(todo)}편')
    for i, r in enumerate(todo, 1):
        s = int(r['series'])
        if s in prev and prev[s].get('next_cnts'):
            out.append(prev[s])
            print(f"  [{i:>3}/{len(todo)}] #{s:<4} 이미 있음 {prev[s]['next_cnts']}")
            continue
        nt = r['next_title']
        hits, _ = nl_search(norm(nt)[:14], pause=args.pause)
        if not hits:                            # 제목이 길거나 OCR이 틀어졌을 때
            hits, _ = nl_search(norm(nt)[:6], pause=args.pause)
        cnts, got_title, how = pick(hits, nt, r['tonggwon'])
        rec = {'series': s, 'tonggwon': r['tonggwon'], 'publish_date': r['publish_date'],
               'title': r['title'], 'last_held': r['last_held'],
               'next_title': nt, 'next_page': r['next_page'],
               'next_cnts': cnts or '', 'next_title_nl': got_title or '',
               'how': how, 'downloaded': ''}
        if cnts:
            found += 1
            if apply_:
                row = {'cnts_id': cnts, 'kolis_no': '', 'title': got_title,
                       'author_hangul': '', 'author_hanja': '',
                       'publisher': '天道敎會月報社',
                       'pub_date': r['publish_date'].replace('-', ''),
                       'holding': '디지털도서관 디지털자료실', 'page_count_meta': '',
                       'format': '온라인자료', 'data_class_cd': 'CH4B',
                       'has_origin_link': '1', 'refworks_sp': '',
                       'list_idx': '1', 'page_num': '1',
                       'source_url': f'https://www.nl.go.kr/NL/contents/search.do?'
                                     f'viewKey={cnts}&viewType=C&category=기사'}
                try:
                    res = art.scrape_one(sess, row, force=False)
                    rec['downloaded'] = str(res)
                except Exception as e:                       # noqa: BLE001
                    rec['downloaded'] = f'오류:{type(e).__name__}'
        else:
            missed += 1
        out.append(rec)
        print(f"  [{i:>3}/{len(todo)}] #{s:<4} 통{r['tonggwon']:<4} {nt[:16]:<18} "
              f"{cnts or '—':<20} {how} {rec['downloaded']}")

    if out:
        with mp.open('w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
            w.writeheader(); w.writerows(out)
    print(f'\n찾음 {found} · 못찾음 {missed} → {mp.name}')
    if not apply_:
        print('--apply 를 주면 지면을 실제로 내려받는다')


if __name__ == '__main__':
    main()
