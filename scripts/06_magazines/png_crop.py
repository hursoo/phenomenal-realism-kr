# -*- coding: utf-8 -*-
"""의존성 없이 PNG를 자른다 (zlib + struct만). 비인터레이스 8비트 전용.

쓰기:  python3 pngcrop.py in.png out.png x y w h [배율]
배율을 주면 최근접 이웃으로 확대한다(정보는 안 늘지만 모델이 보는 픽셀 수가 는다).
"""
import sys, zlib, struct


def chunks(b):
    i = 8
    while i < len(b):
        ln = struct.unpack('>I', b[i:i + 4])[0]
        typ = b[i + 4:i + 8]
        yield typ, b[i + 8:i + 8 + ln]
        i += 8 + ln + 4


def read_png(path):
    b = open(path, 'rb').read()
    idat = b''
    for typ, data in chunks(b):
        if typ == b'IHDR':
            w, h, depth, ctype, comp, filt, inter = struct.unpack('>IIBBBBB', data)
        elif typ == b'IDAT':
            idat += data
        elif typ == b'PLTE':
            plte = data
    assert depth == 8 and inter == 0, f'8비트 비인터레이스만 지원 (depth={depth}, interlace={inter})'
    nch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    raw = zlib.decompress(idat)
    stride = w * nch
    out = bytearray(h * stride)
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        f = raw[p]; p += 1
        line = bytearray(raw[p:p + stride]); p += stride
        if f == 1:
            for i in range(nch, stride):
                line[i] = (line[i] + line[i - nch]) & 255
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif f == 3:
            for i in range(stride):
                a = line[i - nch] if i >= nch else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 255
        elif f == 4:
            for i in range(stride):
                a = line[i - nch] if i >= nch else 0
                c = prev[i - nch] if i >= nch else 0
                bb = prev[i]
                pa, pb, pc = abs(bb - c), abs(a - c), abs(a + bb - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (bb if pb <= pc else c)
                line[i] = (line[i] + pr) & 255
        out[y * stride:(y + 1) * stride] = line
        prev = line
    return w, h, nch, ctype, bytes(out), (plte if ctype == 3 else None)


def write_png(path, w, h, nch, ctype, data, plte=None):
    stride = w * nch
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += data[y * stride:(y + 1) * stride]
    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    body = b'\x89PNG\r\n\x1a\n'
    body += chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, ctype, 0, 0, 0))
    if plte:
        body += chunk(b'PLTE', plte)
    body += chunk(b'IDAT', zlib.compress(bytes(raw), 6))
    body += chunk(b'IEND', b'')
    open(path, 'wb').write(body)


def main():
    src, dst = sys.argv[1], sys.argv[2]
    x, y, cw, ch = map(int, sys.argv[3:7])
    scale = int(sys.argv[7]) if len(sys.argv) > 7 else 1
    w, h, nch, ctype, data, plte = read_png(src)
    x, y = max(0, x), max(0, y)
    cw, ch = min(cw, w - x), min(ch, h - y)
    stride = w * nch
    crop = bytearray()
    for j in range(ch):
        o = (y + j) * stride + x * nch
        crop += data[o:o + cw * nch]
    if scale > 1:
        big = bytearray()
        for j in range(ch):
            row = crop[j * cw * nch:(j + 1) * cw * nch]
            newrow = bytearray()
            for i in range(cw):
                px = row[i * nch:(i + 1) * nch]
                newrow += px * scale
            big += newrow * scale
        crop, cw, ch = big, cw * scale, ch * scale
    write_png(dst, cw, ch, nch, ctype, bytes(crop), plte)
    print(f'{src} ({w}x{h}) → {dst} ({cw}x{ch})  crop=({x},{y}) scale={scale}')


if __name__ == '__main__':
    main()
