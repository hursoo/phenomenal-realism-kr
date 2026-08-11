"""PaddleOCR (PP-OCR) for cheondogyo_wolbo units. v1.1 article-agnostic.

article 폴더(`articles/<slug>/` 또는 `samples/<slug>/`)의 meta.yaml을 읽어 units/ 자동 발견.
units/<unit_id>.png 입력 → ocr/paddle/<unit_id>.txt 산출.

PaddleOCR 3.5+ 필요. 첫 실행 시 모델 자동 다운로드.

Usage:
    python run_paddle_ocr.py --article 01_kwonyu_1911-01
    python run_paddle_ocr.py --article 01_kwonyu_1911-01 --unit unit_3_p2u
    python run_paddle_ocr.py --article 01_kwonyu_1911-01 --lang chinese_cht
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


def discover_units(meta: dict) -> list[dict]:
    return meta.get('units') or meta.get('units_extracted') or []


def extract_texts(res) -> list[str]:
    """Pull rec_texts from a PaddleOCR 3.5 OCRResult."""
    keys_to_try = ('rec_texts', 'rec_text', 'texts')
    for k in keys_to_try:
        try:
            v = res[k]
            if isinstance(v, list):
                return [str(t) for t in v]
        except (KeyError, TypeError):
            pass
    if hasattr(res, 'json'):
        j = res.json
        if isinstance(j, dict):
            for k in keys_to_try:
                if k in j and isinstance(j[k], list):
                    return [str(t) for t in j[k]]
    return []


def main() -> int:
    ap = argparse.ArgumentParser(description='PaddleOCR (article-agnostic) v1.1')
    ap.add_argument('--article', '-a', required=True, help='article slug or path')
    ap.add_argument('--unit', '-u', help='single unit id (default: all units)')
    ap.add_argument('--lang', '-l', default='chinese_cht')
    ap.add_argument('--force', action='store_true', help='overwrite existing OCR outputs')
    args = ap.parse_args()

    article_dir = resolve_article_dir(args.article)
    meta = yaml.safe_load((article_dir / 'meta.yaml').read_text(encoding='utf-8'))
    units = discover_units(meta)
    if args.unit:
        units = [u for u in units if u['id'] == args.unit]
        if not units:
            print(f'ERROR: unit {args.unit} not found', file=sys.stderr)
            return 1

    out_dir = article_dir / 'ocr' / 'paddle'
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f'(article: {article_dir.relative_to(BASE)} | lang: {args.lang} | units: {len(units)})')

    print(f'Initializing PaddleOCR(lang={args.lang}) ... (first run downloads models)', flush=True)
    from paddleocr import PaddleOCR
    ocr = PaddleOCR(
        lang=args.lang,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        enable_mkldnn=False,  # Windows 호환성
    )
    print('Initialized.', flush=True)

    for u in units:
        unit_id = u['id']
        src = article_dir / 'units' / f'{unit_id}.png'
        dst = out_dir / f'{unit_id}.txt'
        if dst.exists() and not args.force:
            print(f'  skip {unit_id} (exists; --force to overwrite)')
            continue
        if not src.exists():
            print(f'  ERROR {unit_id}: image not found at {src}', file=sys.stderr)
            continue
        print(f'\n  OCR: {src.name}', flush=True)
        try:
            output = ocr.predict(str(src))
        except Exception as e:
            print(f'    ERROR -- {type(e).__name__}: {e}', flush=True, file=sys.stderr)
            continue

        all_texts: list[str] = []
        for res in output:
            try:
                res.save_to_json(str(out_dir))
            except Exception as e:
                print(f'    save_to_json failed: {e}', flush=True, file=sys.stderr)
            try:
                res.save_to_img(str(out_dir))
            except Exception as e:
                print(f'    save_to_img failed: {e}', flush=True, file=sys.stderr)
            all_texts.extend(extract_texts(res))

        dst.write_text(
            f'# PaddleOCR (PP-OCR v5, lang={args.lang})\n# Source: {src.name}\n# Detected lines: {len(all_texts)}\n\n'
            + '\n'.join(all_texts)
            + '\n',
            encoding='utf-8',
        )
        print(f'    saved {dst} (lines={len(all_texts)})', flush=True)

    return 0


if __name__ == '__main__':
    sys.exit(main())
