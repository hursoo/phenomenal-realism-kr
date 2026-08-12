# -*- coding: utf-8 -*-
"""단 분리 좌표를 **지면마다 검출한 구분선**으로 다시 채운다. 겹침을 준다.

왜 (Soo 지적 → 전수 확인, 2026-08-12)
    종전 `fill_units_default_dualband.py`는 `divider_y=1180` **고정값**을 전편에 썼다.
    5표본에서 잰 값이었다. 375면을 재 보니 **92.8%가 15px 넘게, 78.4%가 40px(≈한 글자)
    넘게 어긋났고 중앙값이 −69px**다(`detect_divider.py`).

    어긋나면 글자가 사라지는 것이 아니라 **자리를 옮긴다.** 위 단이 자기 마지막 글자
    줄을 잃으면 그것이 아래 단 이미지 맨 위에 얹혀 아래 단 컬럼의 머리에 붙어 읽힌다.
    읽는 차례가 「위 단 전 컬럼 → 아래 단 전 컬럼」이므로 제자리보다 한참 뒤로 밀린다.
    **전사본만 보아서는 보이지 않는다 — 두 엔진이 같은 이미지를 받았으니 마커도 안 선다.**

무엇을 하나
    1. 지면마다 구분선을 검출한다(`detect_divider.find_divider`).
    2. 위 단은 `[0, divider + overlap]`, 아래 단은 `[divider - overlap, 지면 끝]`로 자른다.
       **겹치게 두는 것이 요점이다.** 검출에도 ±20px 오차가 있으므로, 겹치지 않으면
       그 오차가 그대로 손실이 된다. 겹친 글자는 양쪽에 온전히 들어가고, 중복은
       텍스트 층에서 지우면 된다 — **없는 글자는 만들 수 없지만 겹친 글자는 지울 수 있다.**
    3. 구분선을 못 찾은 지면은 **고정값 그대로 두고 표시**한다. 추측하지 않는다.

쓰기
    python3 fill_units_detected_divider.py --series 87-157 [--overlap 40] [--dry-run]

⚠️ 이 스크립트는 `meta.yaml`의 units 좌표를 **덮어쓴다.** 이전 값은 같은 파일의
`units_previous_fixed1180`에 남긴다.
"""
import argparse
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from detect_divider import find_divider                      # noqa: E402

WB = Path('/home/creta/work/0_tnt/hyeonsang/_ocr_experiments/cheondogyo_wolbo_series')
RAW = Path('/home/creta/work/0_tnt/hyeonsang/raw/journals/cheondogyo_wolbo/'
           'nl_bibliography/articles')
LEFT = 80


def parse_range(s):
    out = []
    for part in s.split(','):
        if '-' in part:
            a, b = part.split('-', 1)
            out += list(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return sorted(set(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--series', required=True)
    ap.add_argument('--overlap', type=int, default=40)
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    want = set(parse_range(args.series))
    n_page = n_moved = 0
    for d in sorted((WB / 'articles').iterdir()):
        m = re.match(r'(\d+)_', d.name)
        if not (d.is_dir() and m and int(m.group(1)) in want):
            continue
        mp = d / 'meta.yaml'
        if not mp.exists():
            continue
        meta = yaml.safe_load(mp.read_text(encoding='utf-8'))
        src = (meta.get('source_dir') or '').rstrip('/').split('/')[-1]
        pdir = RAW / src if (RAW / src).is_dir() else RAW / d.name
        pages = meta.get('source_pages') or []
        if not pages or not pdir.is_dir():
            print(f'  ⚠ {d.name}: 지면을 찾지 못했다')
            continue

        units, notes = [], []
        idx = 1
        for p in pages:
            f = pdir / p['file']
            W, H = (int(x) for x in p['pixels'].split('x'))
            n_page += 1
            y = None
            if f.exists():
                try:
                    y, _, _ = find_divider(f)
                except Exception as e:                        # noqa: BLE001
                    notes.append(f"{p['file']}: 검출 실패 {type(e).__name__}")
            if y is None:
                y = 1180
                notes.append(f"{p['file']}: 구분선 미검출 — 고정값 1180")
            else:
                if abs(y - 1180) > 15:
                    n_moved += 1
            up = [LEFT, 0, W, min(H, y + args.overlap)]
            lo = [LEFT, max(0, y - args.overlap), W, H]
            # 이름은 기존 규칙 그대로 — page_001.jpg → unit_N_p1u / unit_N+1_p1l
            pn = int(re.sub(r'\D', '', p['file']) or 1)
            units.append({'id': f'unit_{idx}_p{pn}u', 'file': f'units/unit_{idx}_p{pn}u.png',
                          'page': p['file'], 'crop': up,
                          'pixels': f'{W - LEFT}x{up[3]}', 'role': 'upper',
                          'divider_detected': y, 'overlap': args.overlap})
            idx += 1
            units.append({'id': f'unit_{idx}_p{pn}l', 'file': f'units/unit_{idx}_p{pn}l.png',
                          'page': p['file'], 'crop': lo,
                          'pixels': f'{W - LEFT}x{H - lo[1]}', 'role': 'lower',
                          'divider_detected': y, 'overlap': args.overlap})
            idx += 1

        print(f'  {d.name:<24} 지면 {len(pages)} → 단 {len(units)}'
              + (f'   ⚠ {len(notes)}건' if notes else ''))
        for nt in notes:
            print(f'      {nt}')
        if args.dry_run:
            continue
        if 'units' in meta and 'units_previous_fixed1180' not in meta:
            meta['units_previous_fixed1180'] = meta['units']
        meta['units'] = units
        meta.setdefault('layout', {})['divider_source'] = \
            f'detected per page (detect_divider.py, overlap={args.overlap}px, 2026-08-12)'
        mp.write_text(yaml.dump(meta, allow_unicode=True, sort_keys=False),
                      encoding='utf-8')

    print(f'\n지면 {n_page} · 고정값에서 15px 넘게 옮긴 지면 {n_moved}')
    if not args.dry_run:
        print('다음: cut_units.py로 다시 자르고, 기존 ocr/를 지운 뒤 배치를 다시 돌린다.')


if __name__ == '__main__':
    main()
