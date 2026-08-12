# -*- coding: utf-8 -*-
"""컬럼 검출이 **글줄을 몇 개나 삼켰는지**를 전수로 잰다. API를 쓰지 않는다.

문제 (2026-08-12)
    `detect_columns.find_columns`는 세로 잉크 분포의 골로 글줄을 가른다. 그런데
    글줄 사이 여백이 좁거나 잉크가 번지면 **여러 글줄이 한 상자로 묶인다.**
    C30 `unit_5_p3u`의 실측 폭이 그 실물이다.

        [48, 48, 48, 47, 46, 41, 509, 48, 48, 47]
                                 ↑ 509px 상자 하나가 열 글줄을 삼켰다

    삼켜진 상자를 통째로 확대해 넣으면 모델이 여러 글줄을 뒤섞어 읽거나 일부를
    건너뛴다. 정본 대조에서 한 토막이 통째로 빠진 것이 이 때문이었다.

무엇을 재나
    단마다 (ㄱ) 종전 검출 글줄 수, (ㄴ) 넓은 상자를 쪼갠 뒤의 글줄 수, (ㄷ) 그 차이.
    차이가 곧 **묻혀 있던 글줄 수**다. 엔진이 읽은 `[col NN]` 수도 함께 적어
    셋을 견줄 수 있게 한다.

쓰기
    python3 audit_column_split.py <articles_root> [--min N --max N] [--out split.csv]
"""
import argparse
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from png_crop import read_png                                   # noqa: E402
from detect_columns import gray_profile, smooth, find_columns    # noqa: E402
from reread_columns import split_wide                            # noqa: E402


def engine_cols(adir, unit, eng):
    f = adir / 'ocr' / eng / f'{unit}.txt'
    if not f.exists():
        return ''
    return len(re.findall(r'^\[col\s*\d+\]\s*\S', f.read_text(encoding='utf-8',
                                                              errors='ignore'), re.M))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('articles_root')
    ap.add_argument('--min', type=int, default=0)
    ap.add_argument('--max', type=int, default=9999)
    ap.add_argument('--out', default='')
    args = ap.parse_args()

    root = Path(args.articles_root)
    rows = []
    for d in sorted(root.iterdir()):
        m = re.match(r'(\d+)_', d.name)
        if not (d.is_dir() and m):
            continue
        n = int(m.group(1))
        if not (args.min <= n <= args.max):
            continue
        for png in sorted((d / 'units').glob('*.png')):
            try:
                w, h, nch, ctype, data, plte = read_png(png)
                prof, bg, thr = gray_profile(w, h, nch, data)
                sm = smooth(prof)
                boxes = [(a, b) for a, b in reversed(find_columns(sm)) if b - a >= 18]
                after = split_wide(boxes, prof=sm)
            except Exception as e:                              # noqa: BLE001
                print(f'  ⚠ {d.name}/{png.stem}: {e}', file=sys.stderr)
                continue
            widths = sorted(b - a for a, b in boxes) or [0]
            med = widths[len(widths) // 2]
            widest = widths[-1]
            rows.append(dict(
                series=n, article=d.name, unit=png.stem,
                before=len(boxes), after=len(after), buried=len(after) - len(boxes),
                median_width=med, widest=widest,
                widest_ratio=round(widest / med, 1) if med else 0,
                claude_cols=engine_cols(d, png.stem, 'claude_opus_4_7'),
                gemini_cols=engine_cols(d, png.stem, 'gemini')))

    if not rows:
        print('잰 단이 없다')
        return
    tot_b = sum(r['before'] for r in rows)
    tot_a = sum(r['after'] for r in rows)
    hit = [r for r in rows if r['buried'] > 0]
    print(f'단 {len(rows)} · 글줄 {tot_b} → {tot_a}  '
          f'(**묻혀 있던 글줄 {tot_a - tot_b}, {100 * (tot_a - tot_b) / max(1, tot_a):.1f}%**)')
    print(f'  글줄이 묻힌 단 {len(hit)} ({100 * len(hit) / len(rows):.1f}%)')
    worst = sorted(rows, key=lambda r: -r['buried'])[:12]
    print('\n가장 많이 묻힌 단')
    for r in worst:
        if r['buried'] <= 0:
            break
        print(f"  C{r['series']:<4} {r['article']:<22} {r['unit']:<14} "
              f"{r['before']:>3} → {r['after']:>3} (+{r['buried']})  "
              f"가장 넓은 상자 {r['widest']}px = 중앙값의 {r['widest_ratio']}배")
    if args.out:
        with open(args.out, 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader(); w.writerows(rows)
        print(f'\n→ {args.out}')


if __name__ == '__main__':
    main()
