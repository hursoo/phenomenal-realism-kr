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
import unicodedata
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


def nfkc(s):
    """🔴 **NL 데이터에는 호환 한자가 섞여 있다.**

    2026-08-12에 「第壹百拾二號」의 拾이 `U+F973`(CJK 호환 이체자)이고 보통 쓰는
    `U+62FE`가 아니어서 호수를 못 읽었다. **눈으로는 같은 글자다.** 그래서 30건이
    「호가 다름」으로 잘못 걸렸다. 문자열을 견주기 전에는 반드시 NFKC로 편다.
    """
    return unicodedata.normalize('NFKC', s or '')


def norm(s):
    return re.sub(r'[\s·,.()（）\[\]「」『』]', '', nfkc(s))


# 🔴 호수를 **만들어서 맞추면 안 된다.** NL의 표기가 한 가지가 아니다 —
#   통63은 「第六十三號」인데 통105는 「第壹百五號」, 통116은 「第壹百拾六號」다.
#   백 미만은 보통 자(十)를, 백 이상은 갖은자(壹·拾)를 쓴다. 게다가 「苐」·
#   「天主敎會月報」 같은 오식도 섞인다. 그러니 **만들지 말고 읽는다.**
DIGIT = {'零': 0, '一': 1, '壹': 1, '二': 2, '貳': 2, '兩': 2, '三': 3, '參': 3, '叁': 3,
         '四': 4, '肆': 4, '五': 5, '伍': 5, '六': 6, '陸': 6, '七': 7, '柒': 7,
         '八': 8, '捌': 8, '九': 9, '玖': 9}
UNIT = {'十': 10, '拾': 10, '百': 100, '佰': 100}
HO_RE = re.compile(r'[第苐弟]\s*([零一壹二貳兩三參叁四肆五伍六陸七柒八捌九玖十拾百佰]+)\s*[號号]')


def read_hanja(s):
    """「壹百拾六」 → 116. 십·백 단위를 앞자리 없이 쓰는 옛 표기도 받는다."""
    total, cur = 0, 0
    for ch in s:
        if ch in DIGIT:
            cur = DIGIT[ch]
        elif ch in UNIT:
            u = UNIT[ch]
            if u == 100:
                total += (cur or 1) * 100
            else:
                total += (cur or 1) * 10
            cur = 0
        else:
            return None
    return total + cur


def ho_of(listing_title):
    """목록 제목에서 호수를 읽는다. 못 읽으면 None."""
    m = HO_RE.search(nfkc(listing_title))
    return read_hanja(m.group(1)) if m else None


def pick(hits, title, tonggwon):
    """**호수**가 맞는 것을 고른다. 제목만으로는 연재·동명이 섞인다."""
    tg = int(tonggwon)
    cands = []
    for k, t in hits.items():
        score = 0
        if ho_of(t) == tg:                      # 「[天道敎會月報 第六十三號] 講演 : …」
            score += 10
        if re.search(r'天[道主]敎會月報|천도교회월보', nfkc(t)):  # 「天主敎會月報」 오식도 받는다
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
    if top[0] >= 8:
        return top[1], top[2], '⚠️월보이나 호가 다름'
    return None, None, '못찾음'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--series', default='')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--pause', type=float, default=1.0)
    ap.add_argument('--rescore', action='store_true',
                    help='이미 받아 둔 대응표의 판정만 다시 매긴다 (통신 없음). '
                         '호가 어긋난 줄은 next_cnts를 비워 다음 실행이 다시 찾게 한다')
    args = ap.parse_args()

    if args.rescore:
        mp = REPO / 'next_article_map.csv'
        rows_ = list(csv.DictReader(mp.open(encoding='utf-8-sig')))
        bad = 0
        for r in rows_:
            nl = r.get('next_title_nl') or ''
            if not nl:
                continue
            ho = ho_of(nl)
            wolbo = bool(re.search(r'天[道主]敎會月報|천도교회월보', nfkc(nl)))
            if ho == int(r['tonggwon']) and wolbo:
                r['how'] = '호수일치'
            elif ho == int(r['tonggwon']):
                r['how'] = '⚠️호수만일치'
            else:
                r['how'] = f'🔴호가다름(읽은호={ho})' if wolbo else '🔴월보아님'
                r['next_cnts'] = ''
                bad += 1
        with mp.open('w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rows_[0].keys()))
            w.writeheader(); w.writerows(rows_)
        ok = sum(1 for r in rows_ if r['how'] == '호수일치')
        print(f'{len(rows_)}줄 · 호수일치 {ok} · 물린 것 {bad} (next_cnts를 비웠다)')
        for r in rows_:
            if r['how'].startswith('🔴'):
                print(f"  #{r['series']:<4} 통{r['tonggwon']:<4} {r['next_title'][:16]:<18} "
                      f"{r['how']}  ← {r['next_title_nl'][:46]}")
        return
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
