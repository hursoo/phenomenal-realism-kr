"""article 폴더의 meta.yaml에 정의된 units 좌표대로 페이지를 잘라 units/*.png 산출. v1.0 (2026-05-09)

C2 단 분리 자동화. meta.yaml의 layout·units 작성 후 본 스크립트로 일괄 자르기.

각 unit는:
  - id, file, page (page_NNN.jpg), crop ([x0, y0, x1, y1]), pixels (정보용)
필드를 가진다. 실제 자르기는 PIL.Image.crop. 출력은 units/<unit.id>.png.

Usage:
    python cut_units.py --article 02_信念_1911-04
    python cut_units.py --article 02_信念_1911-04 --force
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

import yaml
from PIL import Image

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r'C:/hp_data/0_tnt/hyeonsang/_ocr_experiments/cheondogyo_wolbo_series')
RAW_BASE = Path(r'C:/hp_data/0_tnt/hyeonsang/raw/journals/cheondogyo_wolbo/nl_bibliography/articles')


def resolve_article_dir(arg: str) -> Path:
    p = Path(arg)
    if p.is_absolute() and p.exists():
        return p
    candidate = BASE / arg
    if candidate.exists():
        return candidate
    for sub in ('articles', 'samples'):
        candidate = BASE / sub / arg
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f'Cannot resolve article path: {arg}')


def main() -> int:
    ap = argparse.ArgumentParser(description='Cut units from page images per meta.yaml')
    ap.add_argument('--article', '-a', required=True, help='article slug or path')
    ap.add_argument('--force', action='store_true', help='overwrite existing unit PNGs')
    args = ap.parse_args()

    article_dir = resolve_article_dir(args.article)
    meta = yaml.safe_load((article_dir / 'meta.yaml').read_text(encoding='utf-8'))

    cnts_id = meta.get('article', {}).get('cnts_id')
    if cnts_id:
        src_dir = RAW_BASE / cnts_id
    else:
        # fallback: 수동 발굴분 — raw 폴더명을 article 폴더명과 동일하게 사용
        src_dir = RAW_BASE / article_dir.name
    if not src_dir.exists():
        print(f'ERROR: source dir not found: {src_dir}', file=sys.stderr)
        return 1

    units = meta.get('units') or []
    if not units:
        print(f'ERROR: no units in meta.yaml (still TODO?)', file=sys.stderr)
        return 1

    out_dir = article_dir / 'units'
    out_dir.mkdir(parents=True, exist_ok=True)

    page_cache: dict[str, Image.Image] = {}
    print(f'(article: {article_dir.relative_to(BASE)} | units: {len(units)})')

    for u in units:
        uid = u['id']
        page_name = u['page']
        crop = u['crop']
        if not isinstance(crop, list) or len(crop) != 4:
            print(f'  ERROR {uid}: invalid crop {crop!r} (expect [x0, y0, x1, y1])', file=sys.stderr)
            continue
        out_path = out_dir / f'{uid}.png'
        if out_path.exists() and not args.force:
            print(f'  skip {uid} (exists; --force to overwrite)')
            continue
        if page_name not in page_cache:
            src_page = src_dir / page_name
            if not src_page.exists():
                print(f'  ERROR {uid}: page {src_page} not found', file=sys.stderr)
                continue
            page_cache[page_name] = Image.open(src_page)
        unit_img = page_cache[page_name].crop(tuple(crop))
        unit_img.save(out_path)
        print(f'  cut {uid}: {page_name} crop={crop} -> {unit_img.size}')

    return 0


if __name__ == '__main__':
    sys.exit(main())
