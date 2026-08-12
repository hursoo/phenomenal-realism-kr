# -*- coding: utf-8 -*-
"""월보 초벌 전사에서 낱말을 세되, 마커가 낱말을 쪼개는 문제를 피한다.

문제
    초벌 전사는 엔진이 갈린 자리를 `⚠️[C:…|G:…]`로 보존한다. 그런데 이 마커가
    **낱말 한가운데를 지날 수 있다.**

        …美善眞이라實⚠️[C:在라ᄒᆞ|G:存이라호]며理性이라…

    여기서 원문은 「實在」인데, 문자열 `實在`를 그냥 찾으면 **걸리지 않는다.**
    Claude는 實在로, Gemini는 實存으로 읽어 마커가 「實」과 「在」 사이를 갈랐기
    때문이다. 곧 **초벌 전사에 대한 단순 문자열 검색은 체계적으로 과소 계수한다.**

방법
    마커를 각각 C쪽·G쪽으로 펴서 **두 판을 만들고 양쪽에서 센다.**
    어느 한 판에라도 걸리면 후보다. `∅`는 「그 엔진은 아무것도 읽지 않았다」이므로
    빈 문자열로 편다.

    이것이 「없다」를 말하기 위한 최소한의 절차다. 한 판에서만 세면 다른 엔진이
    읽은 것을 놓친다.

한계
    두 판을 다 펴도 **두 엔진이 같이 놓친 것은 잡지 못한다.** 이 검색은 후보를
    좁히는 도구이며, 판정은 원본 지면과 대조해야 선다
    (`data/5_magazine_sources/wolbo/verified_passages.md`).

쓰기
    python scripts/06_magazines/screen_wolbo_keywords.py
    python scripts/06_magazines/screen_wolbo_keywords.py --before 1922-02 --kw 三派 唯物 唯心
"""
import argparse
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WOLBO = ROOT / 'data' / '5_magazine_sources' / 'wolbo'

MARKER = re.compile(r'⚠️\[C:(.*?)\|G:(.*?)\]')
DEFAULT_KW = ['三派', '唯物', '唯心', '實在', '物心', '唯物論', '唯心論', '物心合一論']


def unfold(text):
    """마커를 C쪽/G쪽으로 각각 편 두 판을 돌려준다."""
    c = MARKER.sub(lambda m: '' if m.group(1) == '∅' else m.group(1), text)
    g = MARKER.sub(lambda m: '' if m.group(2) == '∅' else m.group(2), text)
    return c, g


def load_index():
    path = WOLBO / 'series_index.csv'
    with open(path, encoding='utf-8-sig') as f:
        return {int(r['series_index']): r for r in csv.DictReader(f)}


def main():
    global WOLBO
    ap = argparse.ArgumentParser()
    ap.add_argument('--before', default='1922-02',
                    help='이 발행일보다 앞선 편만 본다 (YYYY-MM). 전체는 9999-99')
    ap.add_argument('--kw', nargs='*', default=DEFAULT_KW)
    ap.add_argument('--root', default=str(WOLBO),
                    help='articles/·series_index.csv가 있는 폴더. 새로 판독한 편은 '
                         '저장소가 아니라 작업 폴더(_ocr_experiments/…)에 있으므로 '
                         '거기를 가리켜 훑을 수 있다')
    args = ap.parse_args()
    WOLBO = Path(args.root)

    index = load_index()
    scope = [n for n, r in index.items() if r['publish_date'] < args.before]
    print(f'대상: 발행일 < {args.before} → {len(scope)}편 (전체 {len(index)}편)\n')

    hits = {k: [] for k in args.kw}
    scanned = 0
    for d in sorted((WOLBO / 'articles').iterdir()):
        m = re.match(r'(\d+)_', d.name)
        if not d.is_dir() or not m:
            continue
        n = int(m.group(1))
        meta = index.get(n)
        if not meta or meta['publish_date'] >= args.before:
            continue
        scanned += 1
        # ⚠️ 초벌만 읽는다. `transcripts/`에 정본·현대독해본이 함께 있는 편이 있어
        # 통째로 읽으면 같은 글을 두세 번 세게 된다(C01).
        fs = sorted((d / 'transcripts').glob('*draft_v0.md')) or \
             sorted((d / 'transcripts').glob('*.high_fidelity.md'))
        raw = ''.join(f.read_text(encoding='utf-8', errors='ignore') for f in fs)
        c, g = unfold(raw)
        for k in args.kw:
            nc, ng = c.count(k), g.count(k)
            if nc or ng:
                hits[k].append((n, meta['publish_date'], meta['title'], nc, ng))

    print(f'전사본을 읽은 편: {scanned}\n')
    for k in args.kw:
        rows = hits[k]
        print(f'### {k} — {len(rows)}편')
        for n, date, title, nc, ng in rows:
            flag = '  ⚠️ 한 판에만' if (nc == 0) != (ng == 0) else ''
            print(f'  C{n:<3} {date} {title[:26]:<28} C판{nc} G판{ng}{flag}')
        print()

    union = sorted({n for k in args.kw for n, *_ in hits[k]})
    print(f'합집합 후보: {len(union)}편 — ' + ' '.join(f'C{n}' for n in union))


if __name__ == '__main__':
    main()
