# -*- coding: utf-8 -*-
"""단(段) 경계에서 **글자가 잘렸는지**를 전수로 찾는다.

문제 (Soo 지적, 2026-08-12)
    단 분리는 `divider_y=1180` **고정값**으로 지면을 위·아래로 가른다
    (`fill_units_default_dualband.py`). 그런데 지면마다 분리선 위치가 조금씩 다르다.
    문턱이 글줄 한가운데를 지나면 **위 단의 마지막 글자나 아래 단의 첫 글자가 반으로
    잘린다.** 잘린 조각은 판독에서 누락되거나 다른 글자로 읽히는데, **전사본만 보면
    그런 일이 있었는지 알 수 없다.** 마커조차 서지 않는다 — 두 엔진이 똑같이 못 봤기
    때문이다.

    이 손실은 단 하나에 한두 글자지만 **584단에 걸치면 수백 자**가 되고, 하필
    문장 경계에서 일어나므로 문맥으로도 메워지지 않는다.

어떻게 찾나
    글자 상자를 잡아 **이미지 가장자리에 닿아 있는지** 본다.

        · 위 가장자리에 닿은 상자  → 아래 단의 첫 글자가 잘렸을 수 있다
        · 아래 가장자리에 닿은 상자 → 위 단의 마지막 글자가 잘렸을 수 있다

    닿기만 해서는 부족하다. 온전한 글자도 가장자리에 딱 붙을 수 있기 때문이다. 그래서
    **그 상자의 높이가 그 글줄 글자 높이 중앙값의 일정 비율 미만**일 때만 잘림으로 센다
    (기본 0.75). 반쯤 잘린 글자는 높이가 눈에 띄게 작다.

    ⚠️ 이것은 **후보 탐지**다. 확정은 지면을 봐야 한다. 다만 후보가 어디인지 알면
    거기만 보면 된다 — 지금은 어디인지조차 모른다.

쓰기
    python3 detect_cut_glyphs.py <articles_root>              # 전수
    python3 detect_cut_glyphs.py <articles_root> --min 87     # 편 번호 범위
    python3 detect_cut_glyphs.py <articles_root> --out cut.csv

의존성: Pillow(속도 때문). 판정 자체는 픽셀 문턱뿐이다.
"""
import argparse
import csv
import re
import sys
from pathlib import Path


def analyze(png, ratio=0.75, edge=2):
    from PIL import Image
    im = Image.open(png).convert('L')
    w, h = im.size
    px = im.load()
    # 배경 밝기: 가장자리 표본의 중앙값
    samp = sorted(px[x, y] for x in range(0, w, 17) for y in range(0, h, 17))
    bg = samp[len(samp) // 2]
    thr = int(bg * 0.72)

    # 세로 잉크 분포로 글줄 상자
    colprof = [sum(1 for y in range(0, h, 2) if px[x, y] < thr) for x in range(w)]
    cols, run = [], None
    for x, v in enumerate(colprof):
        if v > 1 and run is None:
            run = x
        elif v <= 1 and run is not None:
            if x - run >= 18:
                cols.append((run, x))
            run = None
    if run is not None and w - run >= 18:
        cols.append((run, w))

    hits = []
    for a, b in cols:
        rows = [sum(1 for x in range(a, b) if px[x, y] < thr) for y in range(h)]
        boxes, s = [], None
        for y, v in enumerate(rows):
            if v > 1 and s is None:
                s = y
            elif v <= 1 and s is not None:
                if y - s >= 6:
                    boxes.append((s, y))
                s = None
        if s is not None:
            boxes.append((s, h))
        if len(boxes) < 3:
            continue
        med = sorted(b1 - b0 for b0, b1 in boxes)[len(boxes) // 2]
        for (b0, b1), where in ((boxes[0], '위'), (boxes[-1], '아래')):
            touch = b0 <= edge if where == '위' else b1 >= h - edge
            if touch and (b1 - b0) < med * ratio:
                hits.append(dict(col=len(cols) - cols.index((a, b)), where=where,
                                 height=b1 - b0, median=med,
                                 frac=round((b1 - b0) / med, 2)))
    return hits, len(cols), (w, h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('articles_root')
    ap.add_argument('--min', type=int, default=0)
    ap.add_argument('--max', type=int, default=9999)
    ap.add_argument('--ratio', type=float, default=0.75)
    ap.add_argument('--out', default='')
    args = ap.parse_args()

    root = Path(args.articles_root)
    dirs = []
    for d in sorted(root.iterdir()):
        m = re.match(r'(\d+)_', d.name)
        if d.is_dir() and m and args.min <= int(m.group(1)) <= args.max:
            dirs.append((int(m.group(1)), d))

    rows, n_units, n_hit_units = [], 0, 0
    for n, d in dirs:
        units = sorted((d / 'units').glob('*.png'))
        if not units:
            continue
        art_hits = 0
        for u in units:
            try:
                hits, ncols, size = analyze(u, args.ratio)
            except Exception as e:                            # noqa: BLE001
                print(f'  ⚠ {d.name}/{u.stem}: {e}', file=sys.stderr)
                continue
            n_units += 1
            if hits:
                n_hit_units += 1
                art_hits += len(hits)
                for hh in hits:
                    rows.append(dict(series=n, article=d.name, unit=u.stem,
                                     size=f'{size[0]}x{size[1]}', **hh))
        if art_hits:
            print(f'  C{n:<4} {d.name:<24} 잘림 후보 {art_hits:>3}건 / 단 {len(units)}')

    print(f'\n단 {n_units} 가운데 {n_hit_units}단({100 * n_hit_units / max(1, n_units):.1f}%)에서 '
          f'잘림 후보 {len(rows)}건')
    if rows:
        up = sum(1 for r in rows if r['where'] == '위')
        print(f'  위 가장자리 {up} · 아래 가장자리 {len(rows) - up}')
    if args.out and rows:
        with open(args.out, 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader(); w.writerows(rows)
        print(f'  → {args.out}')


if __name__ == '__main__':
    main()
