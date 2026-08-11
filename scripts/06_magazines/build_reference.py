# -*- coding: utf-8 -*-
"""정본 편에서 **답이 붙은 지면 표본**을 뽑아 판정 기준을 세운다. 의존성 없음.

무엇을 하나
    `marker_decisions.csv`의 각 결정(사람이 확정한 답)을 지면 위 좌표로 되돌려
    **글자 상자의 기하(높이·폭)와 정답을 짝지어** 기록한다.

    이 표가 하는 일은 둘이다.
    1. **기준 세우기** — 예컨대 종성(받침) 유무는 상자 높이에 남는다. 정답이 붙은 표본에서
       그 문턱을 재면 **이미지를 보지 않고도** 후보를 가를 수 있다.
    2. **표본집** — `--crops`를 주면 각 자리를 잘라 저장한다. 「이 모양이면 ᄒᆞᆫ,
       저 모양이면 ᄒᆞ」의 실물 사례가 된다.

쓰기
    python3 build_reference.py <articles_root> <marker_decisions.csv> [--out ref.csv]
                               [--crops <dir>] [--only 종성] [--scale 4] [--window 2]

    <articles_root>는 편 폴더들(`units/`·`ocr/`·`transcripts/`)이 있는 상위 폴더다.
    단 이미지는 저장소에 없으므로(용량) 편자의 작업 폴더를 가리켜야 한다.
"""
import sys, re, csv
from pathlib import Path

sys.path.insert(0, __file__.rsplit('/', 1)[0])
from png_crop import read_png, write_png                       # noqa: E402
from detect_columns import (gray_profile, smooth, find_columns,  # noqa: E402
                            row_profile, find_chars, crop_scale)
from locate_marker import (MK, load_draft, unfold_c, load_cols,  # noqa: E402
                           clean, locate)

JONG = set('ᆨᆩᆪᆫᆬᆭᆮᆯᆰᆱᆲᆳᆴᆵᆶᆷᆸᆹᆺᆻᆼᆽᆾᆿᇀᇁᇂ')


def is_jong(s):
    return s != '' and all(ch in JONG for ch in s)


def kind(c, g):
    """마커 유형을 가른다."""
    c = '' if c == '∅' else c
    g = '' if g == '∅' else g
    if (c == '' and is_jong(g)) or (g == '' and is_jong(c)):
        return '종성'
    if max(len(c), len(g)) >= 15:
        return '대분기'
    if len(c) <= 2 and len(g) <= 2 and re.fullmatch(r'[一-鿿]*', c + g):
        return '한자'
    return '음절'


class UnitCache:
    """단 이미지 한 장의 글줄·글자 상자를 한 번만 계산한다."""

    def __init__(self):
        self.d = {}

    def get(self, png):
        key = str(png)
        if key in self.d:
            return self.d[key]
        w, h, nch, ctype, data, plte = read_png(png)
        prof, bg, thr = gray_profile(w, h, nch, data)
        cols = list(reversed(find_columns(smooth(prof))))
        chars = {}
        for i, (a, b) in enumerate(cols, 1):
            cb = find_chars(row_profile(w, h, nch, data, a, b, thr))
            if cb:
                med = sorted(y1 - y0 for y0, y1 in cb)[len(cb) // 2]
                cb = [t for t in cb if (t[1] - t[0]) >= med * 0.55]
            chars[i] = cb
        v = dict(w=w, h=h, nch=nch, ctype=ctype, data=data, plte=plte,
                 cols=cols, chars=chars)
        self.d[key] = v
        return v


def main():
    root = Path(sys.argv[1])
    dec = Path(sys.argv[2])
    opt = {'--out': 'reference.csv', '--crops': None, '--only': None,
           '--scale': '4', '--window': '2'}
    i = 3
    while i < len(sys.argv):
        if sys.argv[i] in opt:
            opt[sys.argv[i]] = sys.argv[i + 1]; i += 2
        else:
            i += 1

    rows = list(csv.DictReader(open(dec, encoding='utf-8-sig')))
    rows = [r for r in rows if r['verdict'] in ('C', 'G')]
    if opt['--only']:
        rows = [r for r in rows if kind(r['claude'], r['gemini']) == opt['--only']]
    print(f'대상 {len(rows)}건')

    from collections import Counter
    fail = Counter()
    cache = UnitCache()
    crops = Path(opt['--crops']) if opt['--crops'] else None
    if crops:
        crops.mkdir(parents=True, exist_ok=True)
    out, ok, ng = [], 0, 0

    by_art = {}
    for r in rows:
        by_art.setdefault(r['article'], []).append(r)

    for art, rs in sorted(by_art.items()):
        adir = root / art
        if not adir.is_dir():
            print(f'  건너뜀(폴더 없음) {art}'); continue
        draft = load_draft(adir)
        ms = list(MK.finditer(draft))
        cols_txt = load_cols(adir)
        ntext = {(u_, c_): len(t_) for u_, c_, t_ in cols_txt}
        for r in rs:
            k = int(r['marker_index'])
            if not (0 <= k < len(ms)):
                ng += 1; continue
            m = ms[k]
            pre = clean(unfold_c(draft[:m.start()]))
            post = clean(unfold_c(draft[m.end():m.end() + 90]))
            cval = '' if r['claude'] == '∅' else clean(r['claude'])
            loc, keylen, nhits = locate(cols_txt, pre, cval, post)
            if loc is None:
                fail['문맥못찾음'] += 1; ng += 1; continue
            unit, colno, off = loc
            png = adir / 'units' / f'{unit}.png'
            if not png.exists():
                fail['단이미지없음'] += 1; ng += 1; continue
            u = cache.get(png); u['ntext'] = ntext
            ncol_ocr = max((c_ for u_, c_ in ntext if u_ == unit), default=0)
            ncol_det = len(u['cols'])
            colno_det = colno
            if ncol_ocr and ncol_det and ncol_ocr != ncol_det:
                colno_det = max(1, min(ncol_det, round(colno * ncol_det / ncol_ocr)))
            cb = u['chars'].get(colno_det) or []
            ntxt = u['ntext'].get((unit, colno), 0)
            if not cb:
                fail['상자없음'] += 1; ng += 1; continue
            # 판독 글자 수와 검출 상자 수가 다르면 비례로 맞춘다
            if ntxt and ntxt != len(cb):
                off = int(round(off * len(cb) / ntxt))
            if off >= len(cb):
                fail['순번초과'] += 1; ng += 1; continue
            y0, y1 = cb[off]
            colno = colno_det
            hs = sorted(b - a for a, b in cb)
            med = hs[len(hs) // 2]
            a, b = u['cols'][colno_det - 1]
            out.append(dict(article=art, marker=k, kind=kind(r['claude'], r['gemini']),
                            claude=r['claude'], gemini=r['gemini'], final=r['final'],
                            verdict=r['verdict'], unit=unit, col=colno, char=off + 1,
                            box_h=y1 - y0, col_med_h=med,
                            ratio=round((y1 - y0) / med, 3), col_w=b - a,
                            anchor=keylen, hits=nhits,
                            col_ocr=ncol_ocr, col_det=ncol_det,
                            flag=('' if (ncol_ocr == ncol_det and ntxt == len(cb)
                                         and nhits <= 1) else '⚠️')))
            ok += 1
            if crops:
                win = int(opt['--window']); sc = int(opt['--scale'])
                s = max(0, off - win); e = min(len(cb) - 1, off + win)
                x = max(0, a - 4); cw = min(u['w'], b + 4) - x
                y = max(0, cb[s][0] - 4); ch = min(u['h'], cb[e][1] + 4) - y
                buf, w2, h2 = crop_scale(u['w'], u['h'], u['nch'], u['data'],
                                         x, y, cw, ch, sc)
                fin = (r['final'] or 'NUL').replace('/', '_')[:8]
                write_png(crops / f"{art}_m{k:04d}_{r['verdict']}_{fin}.png",
                          w2, h2, u['nch'], u['ctype'], bytes(buf), u['plte'])
        print(f'  {art:<22} {len(rs):>4}건 → 누적 성공 {ok}')

    with open(opt['--out'], 'w', newline='', encoding='utf-8-sig') as f:
        wr = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        wr.writeheader(); wr.writerows(out)
    print(f'\n성공 {ok} · 실패 {ng}  {dict(fail)} → {opt["--out"]}')


if __name__ == '__main__':
    main()
