# -*- coding: utf-8 -*-
"""지면마다 **진짜 단 구분선**을 찾아, 단 분리에 쓴 값과 얼마나 어긋났는지 잰다.

문제 (Soo 지적, 2026-08-12)
    단 분리는 `divider_y=1180` **고정값**으로 위·아래를 갈랐다
    (`fill_units_default_dualband.py` — 5표본에서 잰 값을 전편에 그대로 적용).
    그런데 지면마다 구분선 위치가 다르다. 고정값이 진짜 구분선보다 **위로 잡히면**
    위 단은 마지막 글줄의 끝 글자들을 잃고, 그 글자들은 아래 단의 맨 위에 얹혀
    엉뚱한 자리에서 읽힌다. **아래로 잡히면** 반대로 아래 단의 첫 글자들이 위 단
    꼬리에 붙는다.

    어느 쪽이든 전사본만 보아서는 알 수 없다. 마커조차 서지 않는다 — 두 엔진이 같은
    이미지를 받았으므로 똑같이 어긋난다.

어떻게 찾나
    세로 방향 잉크 분포에서 **지면 한가운데의 가장 넓은 흰 띠**를 찾는다. 이 잡지의
    구분선은 가는 물결선(`divider_kind: thin_wavy_line`)이라 선 자체는 잉크가 얇고
    위아래로 여백이 넓다. 흰 띠의 한가운데를 구분선으로 본다.

    찾은 값과 `meta.yaml`이 실제로 쓴 경계를 견주어 **어긋남(offset)**을 낸다.

쓰기
    python3 detect_divider.py <articles_root> [--min N --max N] [--out div.csv]
    python3 detect_divider.py <articles_root> --tol 15      # 허용 오차

의존성: Pillow.
"""
import argparse
import csv
import re
import sys
from pathlib import Path

import yaml


def find_divider(png, lo=0.38, hi=0.62):
    from PIL import Image
    im = Image.open(png).convert('L')
    w, h = im.size
    px = im.load()
    samp = sorted(px[x, y] for x in range(0, w, 23) for y in range(0, h, 23))
    bg = samp[len(samp) // 2]
    thr = int(bg * 0.72)
    y0, y1 = int(h * lo), int(h * hi)
    ink = [sum(1 for x in range(0, w, 3) if px[x, y] < thr) for y in range(y0, y1)]
    # 잉크가 거의 없는 가장 긴 구간
    best = (0, None)
    run = None
    for i, v in enumerate(ink + [999]):
        if v <= 2 and run is None:
            run = i
        elif v > 2 and run is not None:
            if i - run > best[0]:
                best = (i - run, (run, i))
            run = None
    if best[1] is None:
        return None, h, bg
    a, b = best[1]
    return y0 + (a + b) // 2, h, bg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('articles_root')
    ap.add_argument('--raw', default='/home/creta/work/0_tnt/hyeonsang/raw/journals/'
                                     'cheondogyo_wolbo/nl_bibliography/articles')
    ap.add_argument('--min', type=int, default=0)
    ap.add_argument('--max', type=int, default=9999)
    ap.add_argument('--tol', type=int, default=15)
    ap.add_argument('--out', default='')
    args = ap.parse_args()

    root, raw = Path(args.articles_root), Path(args.raw)
    rows = []
    for d in sorted(root.iterdir()):
        m = re.match(r'(\d+)_', d.name)
        if not (d.is_dir() and m and (d / 'meta.yaml').exists()):
            continue
        n = int(m.group(1))
        if not (args.min <= n <= args.max):
            continue
        meta = yaml.safe_load((d / 'meta.yaml').read_text(encoding='utf-8'))
        src = meta.get('source_dir', '')
        cnts = src.rstrip('/').split('/')[-1] if src else ''
        pdir = raw / cnts
        if not pdir.is_dir():
            pdir = raw / d.name                      # 수동 발굴분
        if not pdir.is_dir():
            continue
        # 지면별로 실제 쓴 경계 = 위 단 crop의 y1
        # 위 단(y0=0)의 crop y1이 곧 쓴 경계다. 다만 **단이 하나뿐인 지면**
        # (y1이 지면 높이와 같음)은 가른 적이 없으므로 검사 대상이 아니다.
        hgt = {p['file']: int(p['pixels'].split('x')[1])
               for p in (meta.get('source_pages') or []) if p.get('pixels')}
        used = {}
        for u in (meta.get('units') or []):
            c, pg = u.get('crop'), u.get('page')
            if c and len(c) == 4 and c[1] == 0:
                if hgt.get(pg) and c[3] >= hgt[pg] - 40:
                    continue                      # 단일 밴드 지면
                used[pg] = c[3]
        for pg, y_used in sorted(used.items()):
            f = pdir / pg
            if not f.exists():
                continue
            try:
                y_true, h, bg = find_divider(f)
            except Exception as e:                    # noqa: BLE001
                print(f'  ⚠ {d.name}/{pg}: {e}', file=sys.stderr)
                continue
            if y_true is None:
                continue
            off = y_used - y_true
            rows.append(dict(series=n, article=d.name, page=pg, height=h,
                             used=y_used, detected=y_true, offset=off))
    bad = [r for r in rows if abs(r['offset']) > args.tol]
    print(f'지면 {len(rows)} 검사 · 어긋남 {args.tol}px 초과 **{len(bad)}면 '
          f'({100 * len(bad) / max(1, len(rows)):.1f}%)**')
    if rows:
        offs = sorted(r['offset'] for r in rows)
        print(f'  어긋남 중앙값 {offs[len(offs)//2]:+}px · '
              f'최소 {offs[0]:+} · 최대 {offs[-1]:+}')
    for r in sorted(bad, key=lambda r: -abs(r['offset']))[:15]:
        print(f"  C{r['series']:<4} {r['article']:<24} {r['page']} "
              f"쓴값 {r['used']} · 실제 {r['detected']} → **{r['offset']:+}px**")
    if args.out and rows:
        with open(args.out, 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader(); w.writerows(rows)
        print(f'  → {args.out}')


if __name__ == '__main__':
    main()
