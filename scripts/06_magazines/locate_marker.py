# -*- coding: utf-8 -*-
"""마커 번호만 주면 그 자리의 지면 조각을 잘라 준다. 의존성 없음.

왜
    초벌의 `⚠️[C:…|G:…]` 마커를 판정하려면 그 자리의 지면을 봐야 하는데, 지면 전체나
    단(段) 밴드로는 종성이 판독되지 않는다(`marker_resolution_experiment.md` §3).
    **글줄 하나에서 대여섯 글자만 잘라 3~4배로** 넣어야 보인다.
    이 스크립트가 「마커 → 그 조각」을 잇는다.

어떻게
    Claude OCR 출력에 **`[col NN]` 글줄 태그가 이미 들어 있다.**

        [col 01] 息ᄒᆞ야死ᄒᆞ而已라ᄒᆞ니果然吾人의生命은
        [col 02] 短ᄒᆞ니라然ᄒᆞ나短ᄒᆞ生命됨을不拘ᄒᆞ고同

    그리고 초벌의 마커 C쪽은 이 텍스트에서 온 것이므로, 마커 앞 문맥을 이 텍스트에서
    찾으면 **어느 unit · 몇 번 글줄 · 글줄 안 몇 번째 글자**인지가 바로 나온다.
    나머지는 `detect_columns.py`가 잡은 상자에서 그 글자를 꺼내는 일이다.

    세로쓰기이므로 글줄은 **오른쪽부터** 1번이고, `[col 01]`도 오른쪽 첫 줄이다.
    둘의 번호가 같은 방향이라 그대로 맞는다.

쓰기
    python3 locate_marker.py <article_dir> <marker_index> [out.png]
    python3 locate_marker.py <article_dir> 60 out.png --window 3 --scale 4
    python3 locate_marker.py <article_dir> --list          # 마커 목록만

    <article_dir>는 `units/`·`ocr/claude_opus_4_7/`·`transcripts/`를 가진 편 폴더다.

한계
    · 면주·캡션이 글줄로 잡히면 글자 번호가 밀린다. 높이가 유별나게 작은 상자는
      버리지만 완전하지 않다. 잘린 조각이 엉뚱하면 `--nudge`로 ±n 글자 옮긴다.
    · 판독이 글자를 빠뜨린 자리에서는 그만큼 어긋난다. 창을 넓게(`--window`) 잡으면 된다.
"""
import sys, re
from pathlib import Path

sys.path.insert(0, __file__.rsplit('/', 1)[0])
from png_crop import read_png, write_png            # noqa: E402
from detect_columns import (gray_profile, smooth, find_columns,   # noqa: E402
                            row_profile, find_chars, crop_scale)

MK = re.compile(r'⚠️\[C:(.*?)\|G:(.*?)(?:\|P:[^\]]*)?\]')
COL = re.compile(r'^\[col (\d+)\]\s*(.*)$', re.M)


def load_draft(adir):
    fs = list((adir / 'transcripts').glob('*draft_v0.md'))
    if not fs:
        sys.exit('초벌(draft_v0)이 없다')
    t = re.sub(r'^---.*?\n---\n', '', fs[0].read_text(encoding='utf-8'), flags=re.S)
    # 본문만: [body] 뒤. 없으면 전체
    if '[body]' in t:
        t = t.split('[body]', 1)[1]
    return t


def unfold_c(s):
    return MK.sub(lambda m: '' if m.group(1) == '∅' else m.group(1), s)


def load_cols(adir, engine='claude_opus_4_7'):
    """[(unit_stem, col_no, 글자열), …] — 판독 순서 그대로."""
    out = []
    for f in sorted((adir / 'ocr' / engine).glob('unit_*.txt')):
        for m in COL.finditer(f.read_text(encoding='utf-8', errors='ignore')):
            txt = re.sub(r'\s', '', m.group(2))
            if txt:
                out.append((f.stem, int(m.group(1)), txt))
    if not out:
        sys.exit(f'{engine}의 [col NN] 태그를 찾지 못했다')
    return out


def clean(s):
    return re.sub(r'\s|<\d+>|\[[^\]]*\]', '', s)


def locate(cols, pre, mid, post):
    """마커 앞·C값·뒤를 **함께** 맞춘다. 앞만 쓰면 면주 침입 때문에 자리를 놓친다.

    반환: ((unit, col, offset), 쓴 닻 길이, 후보 수)
    """
    flat, index = [], []
    for u, c, t_ in cols:
        for i, ch in enumerate(t_):
            flat.append(ch); index.append((u, c, i))
    flat = ''.join(flat)

    def at(p):
        return index[min(p, len(index) - 1)]

    # 앞 n자 + C값 + 뒤 n자 가 통째로 맞는 자리를 찾는다
    for n in (12, 10, 8, 6, 5, 4, 3):
        if len(pre) < n or len(post) < n:
            continue
        key = pre[-n:] + mid + post[:n]
        hits = [m.start() for m in re.finditer(re.escape(key), flat)]
        if hits:
            return at(hits[0] + n), n * 2 + len(mid), len(hits)
    # 그래도 안 되면 앞만으로 (예전 방식)
    for n in (24, 18, 14, 10, 8, 6, 4):
        if len(pre) < n:
            continue
        hits = [m.start() for m in re.finditer(re.escape(pre[-n:]), flat)]
        if hits:
            return at(hits[0] + n), n, len(hits)
    return None, 0, 0


def main():
    adir = Path(sys.argv[1])
    if not adir.is_dir():
        sys.exit(f'폴더가 없다: {adir}')
    args = sys.argv[2:]
    opt = {'--window': '3', '--scale': '4', '--nudge': '0', '--pad': '4',
           '--engine': 'claude_opus_4_7'}
    pos = []
    i = 0
    while i < len(args):
        if args[i] in opt:
            opt[args[i]] = args[i + 1]; i += 2
        else:
            pos.append(args[i]); i += 1

    draft = load_draft(adir)
    ms = list(MK.finditer(draft))

    if not pos or pos[0] == '--list':
        print(f'{adir.name} · 마커 {len(ms)}개')
        for k, m in enumerate(ms):
            c, g = m.group(1), m.group(2).split('|P:')[0]
            l = clean(unfold_c(draft[max(0, m.start() - 24):m.start()]))[-16:]
            print(f'  #{k:<4} …{l}⟦A:{c[:12]}│B:{g[:12]}⟧')
        return

    k = int(pos[0])
    out = pos[1] if len(pos) > 1 else f'marker_{k}.png'
    if not (0 <= k < len(ms)):
        sys.exit(f'마커 번호는 0~{len(ms) - 1}')
    m = ms[k]
    c, g = m.group(1), m.group(2).split('|P:')[0]
    tail = clean(unfold_c(draft[:m.start()]))
    head = clean(unfold_c(draft[m.end():m.end() + 90]))
    cval = '' if c == '∅' else clean(c)

    cols = load_cols(adir, opt['--engine'])
    (loc, keylen, nhits) = locate(cols, tail, cval, head)
    if loc is None:
        sys.exit('판독 텍스트에서 마커 자리를 찾지 못했다 (문맥이 너무 짧거나 어긋남)')
    unit, colno, off = loc
    off += int(opt['--nudge'])

    png = adir / 'units' / f'{unit}.png'
    if not png.exists():
        sys.exit(f'단 이미지가 없다: {png}')
    w, h, nch, ctype, data, plte = read_png(png)
    prof, bg, thr = gray_profile(w, h, nch, data)
    boxes_x = list(reversed(find_columns(smooth(prof))))
    if not (1 <= colno <= len(boxes_x)):
        sys.exit(f'{unit}에서 글줄 {colno}을 찾지 못했다 (검출 {len(boxes_x)}개)')
    a, b = boxes_x[colno - 1]
    chars = find_chars(row_profile(w, h, nch, data, a, b, thr))
    # 면주처럼 유별나게 작은 상자는 버린다
    if chars:
        med = sorted(y1 - y0 for y0, y1 in chars)[len(chars) // 2]
        chars = [(y0, y1) for y0, y1 in chars if (y1 - y0) >= med * 0.55]
    if not chars:
        sys.exit('글자 상자를 찾지 못했다')

    win = int(opt['--window'])
    s = max(0, min(off, len(chars) - 1) - win)
    e = min(len(chars) - 1, min(off, len(chars) - 1) + win)
    pad, scale = int(opt['--pad']), int(opt['--scale'])
    x = max(0, a - pad); cw = min(w, b + pad) - x
    y = max(0, chars[s][0] - pad); chh = min(h, chars[e][1] + pad) - y
    buf, cw2, ch2 = crop_scale(w, h, nch, data, x, y, cw, chh, scale)
    write_png(out, cw2, ch2, nch, ctype, bytes(buf), plte)

    ctx = clean(unfold_c(draft[m.end():m.end() + 20]))[:10]
    print(f'마커 #{k}  ⟦A:{c}│B:{g}⟧')
    print(f'  문맥      …{tail[-14:]} ⟦?⟧ {ctx}…')
    print(f'  자리      {unit} · 글줄 {colno} · 글자 {off + 1}/{len(chars)}'
          f'   (닻 {keylen}자{", ⚠️ 중복 " + str(nhits) + "곳" if nhits > 1 else ""})')
    print(f'  → {out}  {cw2}x{ch2} (글자 {s + 1}~{e + 1}, ×{scale})')
    if max(cw2, ch2) > 1200:
        print('  ⚠️ 크다 — --window를 줄이세요')


if __name__ == '__main__':
    main()
