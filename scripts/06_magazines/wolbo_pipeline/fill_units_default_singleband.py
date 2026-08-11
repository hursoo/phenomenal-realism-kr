"""Phase 2.1 단 분리 일괄 — 기본 single-band layout 적용 (1919-1922 article 용). v1.0 (2026-05-09)

1919-1922 article 기본 가정: single-band (1 unit per page), 분리선 없음.
5표본 #60·#61·#75 + 점검 #45·46·47·48·49·56·66·70·71·72·73·74로 검증된 패턴.

Usage:
    python fill_units_default_singleband.py --series 45-74 --skip 60
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
import yaml

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

BASE = Path(r'C:/hp_data/0_tnt/hyeonsang/_ocr_experiments/cheondogyo_wolbo_series')
LEFT_MARGIN = 80
RIGHT_MARGIN = 1500


def fill_one(article_dir: Path) -> bool:
    meta_path = article_dir / 'meta.yaml'
    if not meta_path.exists():
        print(f'  ! no meta.yaml in {article_dir.name}')
        return False
    text = meta_path.read_text(encoding='utf-8')
    meta = yaml.safe_load(text)
    pages = meta.get('source_pages', [])
    if not pages:
        print(f'  ! no source_pages in {article_dir.name}')
        return False
    units = []
    for i, p in enumerate(pages, start=1):
        try:
            w_str, h_str = p['pixels'].split('x')
            h = int(h_str)
        except Exception:
            print(f'  ! bad pixels {p.get("pixels")} in {article_dir.name}')
            return False
        unit_id = f'unit_{i}_p{i}'
        if i == 1:
            role = 'start'
        elif i == len(pages):
            role = 'tail'
        else:
            role = 'continuation'
        units.append({
            'id': unit_id,
            'file': f'units/{unit_id}.png',
            'page': p['file'],
            'crop': [LEFT_MARGIN, 0, RIGHT_MARGIN, h],
            'pixels': f'{RIGHT_MARGIN-LEFT_MARGIN}x{h}',
            'role': role,
            'contains': 'TODO (OCR 후 자동 판단)',
        })
    meta['layout'] = {
        'page_orientation': 'vertical_writing',
        'bands_per_page': 1,
        'divider_kind': 'none',
        'divider_y': None,
        'layout_type': 'single_band',
        'reading_order': 'page_then_next',
        'body_left_margin': LEFT_MARGIN,
        'hanja_ratio_estimate': '~0.70',
        'oldhangul_density': 'low',
    }
    meta['units'] = units
    meta['excluded'] = [
        {'region': '모든 페이지 좌측 가장자리 (x<80)', 'reason': '부속 — 페이지 헤더(잡지명·기사명 running title) + 페이지번호'},
        {'region': '마지막 p 본문 끝 이후 (장식 그림·「未完」 등)', 'reason': '본 기사 본문 외 영역. OCR 후 검증.'},
    ]
    meta['processing_state']['phase_2_1_unit_extraction'] = 'completed (2026-05-09, default single-band 적용 — 1919-1922 layout 검증 후)'
    new_text = yaml.dump(meta, allow_unicode=True, sort_keys=False, default_flow_style=False)
    new_text = '# Filled by fill_units_default_singleband.py (2026-05-09): default single-band\n' + new_text
    meta_path.write_text(new_text, encoding='utf-8')
    print(f'  OK {article_dir.name}: {len(units)} units (single-band)')
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--article')
    ap.add_argument('--series')
    ap.add_argument('--skip', default='')
    args = ap.parse_args()
    skip = set(int(x) for x in args.skip.split(',') if x.strip())
    if args.article:
        for sub in ('articles', 'samples'):
            d = BASE / sub / args.article
            if d.exists():
                fill_one(d); return
        print(f'! not found: {args.article}'); sys.exit(1)
    if args.series:
        if '-' in args.series:
            lo, hi = args.series.split('-')
            rng = range(int(lo), int(hi)+1)
        else:
            rng = [int(args.series)]
        ok = 0
        for n in rng:
            if n in skip:
                print(f'  -- skip #{n}'); continue
            matches = list((BASE / 'articles').glob(f'{n:02d}_*'))
            if not matches:
                print(f'  ! #{n} no folder'); continue
            if fill_one(matches[0]):
                ok += 1
        print(f'== {ok} filled (single-band)')


if __name__ == '__main__':
    main()
