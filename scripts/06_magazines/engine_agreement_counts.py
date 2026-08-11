# -*- coding: utf-8 -*-
"""미검수 코퍼스에서 정직하게 말할 수 있는 빈도 — 엔진 합의 수준별 구간.

문제
    월보 전사는 대부분 미검수 초벌이라 「이 낱말이 N회 나온다」를 단언할 수 없다.
    그러나 **아무 말도 못 하는 것은 아니다.**

방법
    각 편의 **엔진 원출력을 따로** 세어 합의 수준을 나눈다.

        하한(확실)   두 엔진이 모두 읽은 횟수 = min(claude, gemini)
        상한(가능)   하나라도 읽은 횟수       = max(claude, gemini)
        불확실       상한 − 하한

    「N회」 대신 **「하한 N회, 상한 M회」**로 적으면 초벌 위에서도 정직하다.
    특히 **하한이 0이고 상한도 0**이면 「두 엔진이 모두 못 읽었다」이고, 이것이
    미검수 자료에서 「없다」에 가장 가까운 진술이다.

    합의본(draft_v0)만 세면 이 구간이 보이지 않는다. 마커가 낱말을 쪼개
    과소 계수하기 때문이다(`screening_1922.md` §2).

쓰기
    python3 engine_agreement_counts.py <wolbo_dir> 三派 唯物 唯心 實在 [--before 1922-02]
    python3 engine_agreement_counts.py <wolbo_dir> 生命 --before 9999 --per-article
"""
import sys, re, csv
from pathlib import Path

HDR = re.compile(r'^#.*$', re.M)
TAG = re.compile(r'^\[(section|title|author|col \d+)\]\s*', re.M)


def body(path):
    t = path.read_text(encoding='utf-8', errors='ignore')
    t = HDR.sub('', t)
    t = TAG.sub('', t)
    return re.sub(r'\s', '', t)


def engine_text(adir, engine):
    d = adir / 'ocr' / engine
    if not d.is_dir():
        return None
    fs = sorted(d.glob('unit_*.txt'))
    return ''.join(body(f) for f in fs) if fs else None


def main():
    root = Path(sys.argv[1])
    opt = {'--before': '1922-02', '--per-article': False, '--where': False}
    kws, i = [], 2
    while i < len(sys.argv):
        a = sys.argv[i]
        if a == '--before':
            opt['--before'] = sys.argv[i + 1]; i += 2
        elif a in ('--per-article', '--where'):
            opt[a] = True; i += 1
        else:
            kws.append(a); i += 1

    idx = {int(r['series_index']): r
           for r in csv.DictReader(open(root / 'series_index.csv', encoding='utf-8-sig'))}

    tot = {k: [0, 0, 0] for k in kws}          # [하한, 상한, 편수(상한>0)]
    rows = []
    scanned = 0
    for d in sorted((root / 'articles').iterdir()):
        m = re.match(r'(\d+)_', d.name)
        if not d.is_dir() or not m:
            continue
        n = int(m.group(1))
        meta = idx.get(n)
        if not meta or meta['publish_date'] >= opt['--before']:
            continue
        c = engine_text(d, 'claude_opus_4_7')
        g = engine_text(d, 'gemini')
        if c is None and g is None:
            continue
        scanned += 1
        rec = dict(series=n, date=meta['publish_date'], title=meta['title'][:24])
        for k in kws:
            a = c.count(k) if c else 0
            b = g.count(k) if g else 0
            lo, hi = min(a, b), max(a, b)
            rec[k] = f'{lo}~{hi}' if lo != hi else str(lo)
            tot[k][0] += lo; tot[k][1] += hi
            tot[k][2] += 1 if hi else 0
        rows.append(rec)

    print(f'대상: 발행일 < {opt["--before"]} · 엔진 원출력이 있는 {scanned}편 '
          f'(Claude + Gemini)\n')
    print(f"{'낱말':<10}{'하한':>7}{'상한':>7}{'불확실':>8}{'걸린 편':>8}")
    for k in kws:
        lo, hi, ne = tot[k]
        print(f'{k:<10}{lo:>7}{hi:>7}{hi - lo:>8}{ne:>8}')

    if opt['--per-article']:
        print('\n편별 (상한이 0인 편은 뺀다)')
        head = f"{'편':<5}{'게재':<11}{'제목':<26}" + ''.join(f'{k:>10}' for k in kws)
        print(head)
        for r in rows:
            if all(r[k] == '0' for k in kws):
                continue
            print(f"C{r['series']:<4}{r['date']:<11}{r['title'][:24]:<26}"
                  + ''.join(f"{r[k]:>10}" for k in kws))

    if opt['--where']:
        print('\n출현 자리 (엔진별 · 문맥 ±14자)')
        for d in sorted((root / 'articles').iterdir()):
            m = re.match(r'(\d+)_', d.name)
            if not d.is_dir() or not m:
                continue
            n = int(m.group(1)); meta = idx.get(n)
            if not meta or meta['publish_date'] >= opt['--before']:
                continue
            for eng in ('claude_opus_4_7', 'gemini'):
                dd = d / 'ocr' / eng
                if not dd.is_dir():
                    continue
                for f in sorted(dd.glob('unit_*.txt')):
                    raw = f.read_text(encoding='utf-8', errors='ignore')
                    for line in raw.splitlines():
                        mm = re.match(r'\[col (\d+)\]\s*(.*)', line)
                        if not mm:
                            continue
                        col, txt = mm.group(1), re.sub(r'\s', '', mm.group(2))
                        for k in kws:
                            for h in re.finditer(re.escape(k), txt):
                                s = max(0, h.start() - 14); e = h.end() + 14
                                print(f"  C{n:<3} {meta['publish_date'][:7]} {f.stem:<14} col{col:<3} "
                                      f"{eng[:6]:<7} {k}  …{txt[s:h.start()]}〖{k}〗{txt[h.end():e]}…")

    print('\n읽는 법')
    print('  하한 = 두 엔진이 모두 읽은 횟수  → 있다고 말해도 되는 최소치')
    print('  상한 = 하나라도 읽은 횟수        → 이보다 많을 수는 없다(판독 누락은 별개)')
    print('  ⚠️ 인용하려면 그 자리를 원본 지면과 대조해야 한다.')


if __name__ == '__main__':
    main()
