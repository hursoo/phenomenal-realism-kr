# -*- coding: utf-8 -*-
"""**단 구성은 건드리지 않고 y 경계만 검출값으로 옮긴다.**

왜 (2026-08-12, 앞선 실패를 고치며)
    `fill_units_detected_divider.py`를 1~86편에 돌렸다가 **43편을 망가뜨렸다.**
    그 스크립트는 「모든 지면은 위·아래 두 단」이라고 전제하고 단 목록을 **새로 짓는다.**
    새 71편에는 맞았으나 기존 86편에는 맞지 않았다.

        ① #45 이후 약 40편은 **한 면에 한 단**이다. 월보가 후기에 조판을 바꿨고
           작업장에 `fill_units_default_singleband.py`가 따로 있는 것이 그 자취다.
           그것을 두 단으로 가르면 없는 구분선을 그어 글을 두 동강 낸다.
        ② #1·#2는 **x 경계를 손으로 좁혀** 두었다(예: `[80,1180,900,2384]` —
           1쪽 하단의 오른쪽만. 왼쪽은 앞 글이다). 전폭으로 넓히면 남의 글이 들어온다.

    교훈은 하나다. **고칠 것만 고친다.** 어긋난 것은 y 경계 하나였는데 단 구성 전체를
    다시 지었다. 고쳐야 할 것보다 넓게 손대면 고치지 않아도 될 것이 망가진다.

무엇을 하나
    편마다 `units_previous_fixed1180`(있으면 그것, 없으면 현재 `units`)을 **그대로 두고**,
    같은 지면에 위 단과 아래 단이 **둘 다 있는 경우에만** 그 사이의 y 경계를 옮긴다.

        위 단 [x0, y0, x1, div + overlap]
        아래 단 [x0, div - overlap, x1, y1]

    x는 손대지 않는다. 단이 하나뿐인 지면(단일 띠)은 손대지 않는다.
    구분선을 못 찾은 지면도 손대지 않는다. **추측하지 않는다.**

쓰기
    python3 refit_divider_inplace.py --series 1-86 --restore   # 먼저 되돌리고
    python3 refit_divider_inplace.py --series 1-86             # 다시 맞춘다
    python3 refit_divider_inplace.py --series 1-86 --dry-run
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
PREV_KEY = 'units_previous_fixed1180'


def parse_range(s):
    out = []
    for part in s.split(','):
        if '-' in part:
            a, b = part.split('-', 1)
            out += list(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return sorted(set(out))


def page_of(u):
    """단 이름에서 지면 번호와 위/아래를 읽는다 — `unit_3_p2u` → (2, 'u')."""
    m = re.search(r'_p(\d+)([ul])', u.get('file', ''))
    return (int(m.group(1)), m.group(2)) if m else (None, None)


def raw_dir(meta, slug):
    src = (meta.get('source_dir') or '').rstrip('/').split('/')[-1]
    for cand in (RAW / src, RAW / slug):
        if cand.is_dir():
            return cand
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--series', required=True)
    ap.add_argument('--overlap', type=int, default=40)
    ap.add_argument('--restore', action='store_true',
                    help='units_previous_fixed1180 으로 되돌리기만 한다')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    want = set(parse_range(args.series))

    n_ed = n_moved = n_pair = n_single = n_nodiv = n_whole = 0
    for d in sorted((WB / 'articles').iterdir()):
        m = re.match(r'(\d+)_', d.name)
        if not (d.is_dir() and m and int(m.group(1)) in want):
            continue
        mp = d / 'meta.yaml'
        if not mp.exists():
            continue
        meta = yaml.safe_load(mp.read_text(encoding='utf-8'))
        base = meta.get(PREV_KEY) or meta.get('units') or []
        if not base:
            continue
        n_ed += 1

        units = [dict(u) for u in base]
        if not args.restore:
            pd_ = raw_dir(meta, d.name)
            by_page = {}
            for i, u in enumerate(units):
                p, side = page_of(u)
                if p is None:
                    n_whole += 1        # `unit_N_pM.png` — 한 면이 통째로 한 단이다
                    continue            # (#45 이후 후기 조판). 손대지 않는다
                by_page.setdefault(p, {})[side] = i
            for p, sides in sorted(by_page.items()):
                if 'u' not in sides or 'l' not in sides:
                    n_single += 1                     # 단이 하나뿐 — 손대지 않는다
                    continue
                n_pair += 1
                jpg = (pd_ / f'page_{p:03d}.jpg') if pd_ else None
                if not (jpg and jpg.exists()):
                    n_nodiv += 1
                    continue
                div, _h, _bg = find_divider(jpg)
                if div is None:
                    n_nodiv += 1
                    continue
                up, lo = units[sides['u']], units[sides['l']]
                old = up['crop'][3]
                up['crop'] = [up['crop'][0], up['crop'][1], up['crop'][2],
                              div + args.overlap]
                lo['crop'] = [lo['crop'][0], max(0, div - args.overlap),
                              lo['crop'][2], lo['crop'][3]]
                up['divider_detected'] = lo['divider_detected'] = True
                if abs(div - old) > 15:
                    n_moved += 1

        if not args.dry_run:
            if PREV_KEY not in meta:
                meta[PREV_KEY] = base
            meta['units'] = units
            mp.write_text(yaml.safe_dump(meta, allow_unicode=True, sort_keys=False),
                          encoding='utf-8')
        print(f'  {d.name:<26} 단 {len(units)}')

    print(f'\n편 {n_ed}')
    if args.restore:
        print('  이전 단 구성으로 되돌렸다. cut_units.py 로 다시 자른다.')
    else:
        print(f'  위·아래가 짝인 지면 {n_pair} (그 가운데 15px 넘게 옮김 {n_moved})')
        print(f'  단이 하나뿐이라 손대지 않은 지면 {n_single}')
        print(f'  구분선을 못 찾아 손대지 않은 지면 {n_nodiv}')
        print(f'  한 면이 통째로 한 단이라 손대지 않은 단 {n_whole} '
              f'(후기 조판 — 이것을 두 단으로 가른 것이 앞선 실패였다)')
        print('  다음: cut_units.py --force 로 다시 자른다.')


if __name__ == '__main__':
    main()
