"""Phase 2.1 단 분리 일괄 — 기본 dual-band L1 layout 적용. v1.0 (2026-05-09)

bootstrap_article.py의 TODO placeholder를 *시기별 batch 일괄 진행*용으로 채움.
1910년대 ~ 1920년대 초 기본 가정: dual-band horizontal_only (L1), divider_y=1180,
crop x=80~1500 (full width), reading_order=snake.

5표본(#1·#2·#20·#32·#40·#75)에서 검증된 패턴. 1920년대 single-band(#60)는 별도 처리 필요 — 본 스크립트는 일괄 적용 후 OCR 결과로 layout 부적절성 검출.

Usage:
    python fill_units_default_dualband.py --article 03_宗敎_1911-06
    python fill_units_default_dualband.py --series 3-29 --skip 10,20
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
DIVIDER_Y = 1180
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
        unit_u_id = f'unit_{2*i-1}_p{i}u'
        unit_l_id = f'unit_{2*i}_p{i}l'
        role_u = 'start' if i == 1 else 'continuation'
        role_l = 'tail' if i == len(pages) else 'continuation'
        units.append({
            'id': unit_u_id,
            'file': f'units/{unit_u_id}.png',
            'page': p['file'],
            'crop': [LEFT_MARGIN, 0, RIGHT_MARGIN, DIVIDER_Y],
            'pixels': f'{RIGHT_MARGIN-LEFT_MARGIN}x{DIVIDER_Y}',
            'role': role_u,
            'contains': 'TODO (OCR 후 자동 판단)',
        })
        units.append({
            'id': unit_l_id,
            'file': f'units/{unit_l_id}.png',
            'page': p['file'],
            'crop': [LEFT_MARGIN, DIVIDER_Y, RIGHT_MARGIN, h],
            'pixels': f'{RIGHT_MARGIN-LEFT_MARGIN}x{h-DIVIDER_Y}',
            'role': role_l,
            'contains': 'TODO (OCR 후 자동 판단)',
        })
    meta['layout'] = {
        'page_orientation': 'vertical_writing',
        'bands_per_page': 2,
        'divider_kind': 'thin_wavy_line',
        'divider_y': DIVIDER_Y,
        'layout_type': 'horizontal_only',
        'reading_order': 'snake',
        'body_left_margin': LEFT_MARGIN,
        'hanja_ratio_estimate': '~0.80',
        'oldhangul_density': 'low_to_mid',
    }
    meta['units'] = units
    meta['excluded'] = [
        {'region': 'p1 上段 우측 (표제 우측 영역, x>?)', 'reason': '본 1편 패턴 가정 — 上段 이전 기사가 표제 우측까지 흘러옴 (OCR 후 검증 갱신)'},
        {'region': '마지막 p 下段 (다음 기사 시작 영역 가능)', 'reason': '본 기사 결말 후 다음 기사 시작 가능. OCR 결과로 검증 후 자르기 갱신.'},
        {'region': '모든 페이지 좌측 가장자리 (x<80)', 'reason': '부속 — 섹션 라벨 + 페이지번호'},
    ]
    if 'ancillary' in meta and meta['ancillary'].get('page_numbers') is None or meta.get('ancillary', {}).get('page_numbers') == []:
        meta['ancillary']['page_numbers'] = [
            {'page': p['file'], 'value': '?', 'hanja': i}
            for i, p in enumerate(pages, start=meta['article'].get('page_in_journal', 0))
        ]
    meta['processing_state']['phase_2_1_unit_extraction'] = 'completed (2026-05-09, default dual-band L1 적용 — OCR 결과로 검증 대기)'
    new_text = yaml.dump(meta, allow_unicode=True, sort_keys=False, default_flow_style=False)
    new_text = '# Filled by fill_units_default_dualband.py (2026-05-09): default dual-band L1\n' + new_text
    meta_path.write_text(new_text, encoding='utf-8')
    print(f'  OK {article_dir.name}: {len(units)} units')
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--article', help='single article slug')
    ap.add_argument('--series', help='range like 3-29 or single 3')
    ap.add_argument('--skip', help='comma-separated series_index to skip', default='')
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
        print(f'== {ok} filled')
    else:
        ap.print_help()


if __name__ == '__main__':
    main()
