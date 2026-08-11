# -*- coding: utf-8 -*-
"""세로쓰기 지면에서 글줄(컬럼) 좌표를 자동으로 잡는다. 의존성 없음(zlib + struct).

왜 필요한가
    마커 판정 가운데 **종성 유무**(`ᄒᆞ` vs `ᄒᆞᆫ`)는 지면 전체나 단(段) 밴드를 통째로
    넣으면 판독되지 않는다. 비전 모델이 큰 이미지를 축소해 처리하면서 글자당 픽셀이
    임계 아래로 떨어져 아래아 밑의 작은 받침이 사라지기 때문이다.
    **컬럼 하나만 잘라 3~4배로 넣으면 보인다**(`marker_resolution_experiment.md` §3).
    이 스크립트는 그 「컬럼 하나」의 좌표를 사람 눈대중 없이 잡는다.

방법
    1. 그레이스케일 → 이진화(임계 = 배경 최빈값에서 아래로 delta)
    2. x축 잉크 밀도 프로파일 (행을 step 간격으로 표본)
    3. 프로파일의 골짜기 = 글줄 사이 여백 → 경계
    4. 폭이 지나치게 넓은 덩어리(사진·도판)는 표시만 하고 컬럼에서 뺀다
    5. 세로쓰기이므로 **오른쪽부터** 1번을 매긴다

쓰기
    python3 detect_columns.py <png>                         # 컬럼 목록
    python3 detect_columns.py <png> --chars 3                # 3번 컬럼의 글자 목록
    python3 detect_columns.py <png> --crop 3 out.png         # 3번 컬럼 전체
    python3 detect_columns.py <png> --crop 3 out.png --chars 9-15 --scale 4

    ⚠️ **컬럼 전체를 넣으면 안 된다.** 4배로 키우면 높이가 4,000px을 넘어 모델 입력에서
    다시 축소되고, 받침이 도로 사라진다. `--chars`로 5~8글자씩 토막내
    **가로세로 200~900px** 안에 들어오게 한다.

한계
    · PNG 8비트 비인터레이스만 읽는다. 원본 지면은 JPG이므로 `units/*.png`를 쓴다.
    · 삽화·초상이 글줄을 가로지르면 그 구간의 경계가 흔들린다. `--min-gap`으로 조절한다.
"""
import sys, struct, zlib

sys.path.insert(0, __file__.rsplit('/', 1)[0])
from png_crop import read_png, write_png  # noqa: E402


def gray_profile(w, h, nch, data, step=3, delta=45):
    """x별 잉크 화소 수. 배경 밝기에서 delta 이상 어두우면 잉크로 센다."""
    stride = w * nch
    # 배경 밝기 = 표본 화소의 최빈값
    hist = [0] * 256
    for y in range(0, h, step * 4):
        row = data[y * stride:(y + 1) * stride]
        for x in range(0, w, 4):
            o = x * nch
            g = row[o] if nch < 3 else (row[o] * 299 + row[o + 1] * 587 + row[o + 2] * 114) // 1000
            hist[g] += 1
    bg = hist.index(max(hist))
    thr = max(0, bg - delta)

    prof = [0] * w
    for y in range(0, h, step):
        row = data[y * stride:(y + 1) * stride]
        if nch == 1:
            for x in range(w):
                if row[x] < thr:
                    prof[x] += 1
        else:
            for x in range(w):
                o = x * nch
                if (row[o] * 299 + row[o + 1] * 587 + row[o + 2] * 114) // 1000 < thr:
                    prof[x] += 1
    return prof, bg, thr


def smooth(p, k=3):
    n = len(p)
    return [sum(p[max(0, i - k):min(n, i + k + 1)]) // (min(n, i + k + 1) - max(0, i - k))
            for i in range(n)]


def find_columns(prof, min_gap=6, min_width=14, ink_ratio=0.12):
    """잉크가 이어지는 구간을 컬럼으로 묶는다."""
    peak = max(prof) if prof else 0
    thr = peak * ink_ratio
    runs, s = [], None
    for i, v in enumerate(prof):
        if v > thr and s is None:
            s = i
        elif v <= thr and s is not None:
            runs.append((s, i)); s = None
    if s is not None:
        runs.append((s, len(prof)))
    # 좁은 틈은 이어 붙인다
    merged = []
    for a, b in runs:
        if merged and a - merged[-1][1] < min_gap:
            merged[-1] = (merged[-1][0], b)
        else:
            merged.append((a, b))
    return [(a, b) for a, b in merged if b - a >= min_width]


def row_profile(w, h, nch, data, x0, x1, thr, step=1):
    """컬럼 안에서 y별 잉크 화소 수."""
    stride = w * nch
    prof = [0] * h
    for y in range(0, h, step):
        row = data[y * stride:(y + 1) * stride]
        c = 0
        for x in range(x0, x1):
            o = x * nch
            g = row[o] if nch < 3 else (row[o] * 299 + row[o + 1] * 587 + row[o + 2] * 114) // 1000
            if g < thr:
                c += 1
        prof[y] = c
    return prof


def find_chars(prof, min_gap=3, min_h=10, ink_ratio=0.06):
    """y 프로파일에서 글자 상자를 뽑는다."""
    peak = max(prof) if prof else 0
    t = peak * ink_ratio
    runs, s = [], None
    for i, v in enumerate(prof):
        if v > t and s is None:
            s = i
        elif v <= t and s is not None:
            runs.append((s, i)); s = None
    if s is not None:
        runs.append((s, len(prof)))
    merged = []
    for a, b in runs:
        if merged and a - merged[-1][1] < min_gap:
            merged[-1] = (merged[-1][0], b)
        else:
            merged.append((a, b))
    return [(a, b) for a, b in merged if b - a >= min_h]


def crop_scale(w, h, nch, data, x, y, cw, ch, scale):
    stride = w * nch
    out = bytearray()
    for j in range(ch):
        o = (y + j) * stride + x * nch
        out += data[o:o + cw * nch]
    if scale > 1:
        big = bytearray()
        for j in range(ch):
            row = out[j * cw * nch:(j + 1) * cw * nch]
            nr = bytearray()
            for k in range(cw):
                nr += row[k * nch:(k + 1) * nch] * scale
            big += nr * scale
        return big, cw * scale, ch * scale
    return out, cw, ch


def main():
    src = sys.argv[1]
    opt = {'--crop': None, '--chars': None, '--scale': '4', '--pad': '4',
           '--min-gap': '6', '--step': '3'}
    out = None
    i = 2
    while i < len(sys.argv):
        a = sys.argv[i]
        if a == '--crop':
            opt['--crop'] = sys.argv[i + 1]; out = sys.argv[i + 2]; i += 3
        elif a in opt:
            opt[a] = sys.argv[i + 1]; i += 2
        else:
            i += 1

    w, h, nch, ctype, data, plte = read_png(src)
    prof, bg, thr = gray_profile(w, h, nch, data, step=int(opt['--step']))
    prof = smooth(prof)
    cols = find_columns(prof, min_gap=int(opt['--min-gap']))
    med = sorted(b - a for a, b in cols)[len(cols) // 2] if cols else 0
    ordered = list(reversed(cols))          # 세로쓰기 = 오른쪽부터

    def col_of(spec):
        n = int(str(spec).split('-')[0]) if opt['--crop'] is None else int(opt['--crop'])
        if not (1 <= n <= len(ordered)):
            sys.exit(f'컬럼 번호는 1~{len(ordered)}')
        return n, ordered[n - 1]

    # (1) 글자 목록만
    if opt['--crop'] is None and opt['--chars'] is not None:
        n = int(opt['--chars']); 
        if not (1 <= n <= len(ordered)):
            sys.exit(f'컬럼 번호는 1~{len(ordered)}')
        a, b = ordered[n - 1]
        ch_boxes = find_chars(row_profile(w, h, nch, data, a, b, thr))
        print(f'{src} · 컬럼 {n} (x={a}~{b}) · 글자 {len(ch_boxes)}개')
        print(f"{'번호':>4}{'y0':>7}{'y1':>7}{'높이':>6}")
        for k, (y0, y1) in enumerate(ch_boxes, 1):
            print(f'{k:>4}{y0:>7}{y1:>7}{y1 - y0:>6}')
        print(f'\n예:  python3 detect_columns.py {src} --crop {n} out.png --chars 1-6')
        return

    # (2) 컬럼 목록
    if opt['--crop'] is None:
        print(f'{src}  {w}x{h} {nch}ch · 배경밝기 {bg} · 임계 {thr}')
        print(f'글줄 후보 {len(cols)}개 · 폭 중앙값 {med}px  (오른쪽=1번)\n')
        print(f"{'번호':>4}{'x0':>7}{'x1':>7}{'폭':>6}   비고")
        for n, (a, b) in enumerate(ordered, 1):
            note = '⚠️ 넓다(삽화?)' if med and (b - a) > med * 2.2 else ''
            print(f'{n:>4}{a:>7}{b:>7}{b - a:>6}   {note}')
        print(f'\n예:  python3 detect_columns.py {src} --chars 1')
        return

    # (3) 자르기
    n, (a, b) = col_of(opt['--crop'])
    pad, scale = int(opt['--pad']), int(opt['--scale'])
    x, cw = max(0, a - pad), min(w, b + pad) - max(0, a - pad)
    y, chh, label = 0, h, '전체'
    if opt['--chars']:
        boxes = find_chars(row_profile(w, h, nch, data, a, b, thr))
        s, _, e = opt['--chars'].partition('-')
        s = int(s); e = int(e) if e else s
        if not (1 <= s <= e <= len(boxes)):
            sys.exit(f'글자 번호는 1~{len(boxes)}')
        y = max(0, boxes[s - 1][0] - pad)
        chh = min(h, boxes[e - 1][1] + pad) - y
        label = f'{s}~{e}번 글자'
    buf, cw2, ch2 = crop_scale(w, h, nch, data, x, y, cw, chh, scale)
    write_png(out, cw2, ch2, nch, ctype, bytes(buf), plte)
    warn = '  ⚠️ 크다 — --chars로 토막내세요' if max(cw2, ch2) > 1200 else ''
    print(f'컬럼 {n}/{len(ordered)} · {label} → {out}  {cw2}x{ch2} (×{scale}){warn}')


if __name__ == '__main__':
    main()
