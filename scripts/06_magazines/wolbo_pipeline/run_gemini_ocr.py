"""Gemini 2.5 Pro vision OCR for cheondogyo_wolbo units. v1.1 article-agnostic.

article 폴더(`articles/<slug>/` 또는 `samples/<slug>/`)의 meta.yaml을 읽어 units/ 자동 발견.
units/<unit_id>.png 입력 → ocr/gemini/<unit_id>.txt 산출.

Usage:
    python run_gemini_ocr.py --article 01_勸誘_1911-01
    python run_gemini_ocr.py --article 01_勸誘_1911-01 --unit unit_3_p2u
    python run_gemini_ocr.py --article 01_勸誘_1911-01 --model gemini-2.5-pro
"""
from __future__ import annotations
import argparse
import base64
import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

import yaml

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

ENV_PATH = Path(r'C:/hp_data/0_tnt/.env')
_env = {}
for _line in ENV_PATH.read_text(encoding='utf-8').splitlines():
    _s = _line.strip()
    if not _s or _s.startswith('#') or '=' not in _s:
        continue
    _k, _v = _s.split('=', 1)
    _env[_k.strip()] = _v.strip().strip('"').strip("'")
KEY = _env['GOOGLE_API_KEY']

BASE = Path(r'C:/hp_data/0_tnt/hyeonsang/_ocr_experiments/cheondogyo_wolbo_series')

PROMPT = """이 이미지는 한국 1910s~1920s 활판 인쇄 잡지(천도교회월보)의 한 단(段)이다.
세로쓰기, 우→좌 컬럼 흐름, 한자+한글 혼용(국한문혼용),
옛한글 자모(아래아 ㆍ, ᄒᆞ 결합형 등) 보존 자료다.

다음 규칙으로 텍스트를 추출하라:
1. 컬럼 순서: 우측 -> 좌측. 컬럼 안에서는 위 -> 아래.
2. 옛한글 자모(ᄒᆞ, ᄒᆞᆫ, ᄒᆞᆷ, ᄒᆞ니, ᄒᆞ고, ᄒᆞ야 등)는 원본 그대로 보존. 현대 한글로 변환 금지.
3. 한자는 원본 그대로 보존 (정자/속자 구분 없이).
4. 띄어쓰기는 부여하지 말 것 (원문에 없음).
5. 컬럼별로 [col 01], [col 02], ... 라벨로 구분.
6. 표제/저자명이 있으면 [title]/[author] 별도 라벨.
7. 페이지번호/섹션 표시 같은 부속 정보는 제외.
8. 식별 불확실 글자는 [?] 또는 [?字].

결과는 텍스트만 출력 (설명 없이)."""


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


def call_gemini(image_path: Path, model: str) -> tuple[str, dict]:
    b64 = base64.b64encode(image_path.read_bytes()).decode('ascii')
    body = {
        'contents': [{
            'parts': [
                {'text': PROMPT},
                {'inline_data': {'mime_type': 'image/png', 'data': b64}},
            ]
        }],
        'generationConfig': {
            'maxOutputTokens': 8000,
            'temperature': 0.1,
        },
    }
    data = json.dumps(body).encode('utf-8')
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={KEY}'
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=300) as r:
        resp = json.loads(r.read().decode('utf-8'))
    cand = resp.get('candidates', [{}])[0]
    parts = cand.get('content', {}).get('parts', [])
    text = ''.join(p.get('text', '') for p in parts)
    usage = resp.get('usageMetadata', {})
    return text, usage


def main() -> int:
    ap = argparse.ArgumentParser(description='Gemini vision OCR (article-agnostic) v1.1')
    ap.add_argument('--article', '-a', required=True, help='article slug or path')
    ap.add_argument('--unit', '-u', help='single unit id (default: all units)')
    ap.add_argument('--model', '-m', default='gemini-2.5-pro')
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

    out_dir = article_dir / 'ocr' / 'gemini'
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f'(article: {article_dir.relative_to(BASE)} | model: {args.model} | units: {len(units)})')

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
        print(f'  OCR ({args.model}): {src.name} -> {dst.name}')
        try:
            text, usage = call_gemini(src, args.model)
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8', errors='replace')[:500]
            print(f'    ERROR HTTP {e.code} -- {body}', file=sys.stderr)
            continue
        except Exception as e:
            print(f'    ERROR -- {type(e).__name__}: {e}', file=sys.stderr)
            continue
        header = (
            f'# Gemini {args.model} vision OCR\n'
            f'# Source: {src.name}\n'
            f'# Usage: prompt_tokens={usage.get("promptTokenCount")} candidates_tokens={usage.get("candidatesTokenCount")} total={usage.get("totalTokenCount")}\n\n'
        )
        dst.write_text(header + text + '\n', encoding='utf-8')
        print(f'    saved (chars={len(text)})')

    return 0


if __name__ == '__main__':
    sys.exit(main())
