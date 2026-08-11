"""Anthropic Claude vision OCR for cheondogyo_wolbo units. v1.0 article-agnostic.

article 폴더(`articles/<slug>/`)의 meta.yaml을 읽어 units/ 자동 발견.
units/<unit_id>.png 입력 → ocr/<engine_tag>/<unit_id>.txt 산출.

기본 모델: claude-sonnet-4-6 (engine_tag=sonnet_4_6)
대안: claude-opus-4-7 (engine_tag=claude_opus_4_7)

Usage:
    python run_claude_ocr.py --article 32_人生_1915-08
    python run_claude_ocr.py --article 32_人生_1915-08 --unit unit_3_p2u
    python run_claude_ocr.py --article 32_人生_1915-08 --model claude-opus-4-7
"""
from __future__ import annotations
import argparse
import base64
import sys
import time
from pathlib import Path
import yaml
import anthropic

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
KEY = _env['ANTHROPIC_API_KEY']

BASE = Path(r'C:/hp_data/0_tnt/hyeonsang/_ocr_experiments/cheondogyo_wolbo_series')

MODEL_TO_TAG = {
    'claude-sonnet-4-6': 'sonnet_4_6',
    'claude-opus-4-7': 'claude_opus_4_7',
    'claude-haiku-4-5-20251001': 'haiku_4_5',
}

PROMPT = """이 이미지는 한국 1910s~1920s 활판 인쇄 잡지(천도교회월보)의 한 단(段)이다.
세로쓰기, 우→좌 컬럼 흐름, 한자+한글 혼용(국한문혼용),
옛한글 자모(아래아 ㆍ, ᄒᆞ 결합형 등) 보존 자료다.

다음 규칙으로 텍스트를 추출하라:
1. 컬럼 순서: 우측 → 좌측. 컬럼 안에서는 위 → 아래.
2. 옛한글 자모(ᄒᆞ, ᄒᆞᆫ, ᄒᆞᆷ, ᄒᆞ니, ᄒᆞ고, ᄒᆞ야 등)는 원본 그대로 보존. 현대 한글로 변환 금지.
3. 한자는 원본 그대로 보존 (정자/속자 구분 없이).
4. 띄어쓰기는 부여하지 말 것 (원문에 없음).
5. 컬럼별로 [col 01], [col 02], ... 라벨로 구분.
6. 표제/저자명이 있으면 [title]/[author] 별도 라벨.
7. 섹션 라벨이 있으면 [section] 또는 [section_running].
8. 다음 기사 영역은 [next_article_start] 이후로 분리.
9. 페이지번호 같은 부속 정보는 제외.
10. 식별 불확실 글자는 [?] 또는 [?字].

출력은 위 라벨과 본문만. 서술적 설명·해석 금지."""


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
    raise FileNotFoundError(f'article not found: {arg}')


def call_anthropic(client: anthropic.Anthropic, model: str, image_path: Path, retries: int = 3) -> tuple[str, dict]:
    image_data = base64.standard_b64encode(image_path.read_bytes()).decode('utf-8')
    last_err = None
    for attempt in range(retries):
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=4000,
                system=PROMPT,
                messages=[{
                    'role': 'user',
                    'content': [
                        {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': image_data}},
                        {'type': 'text', 'text': '이 단의 OCR을 위 규칙대로 수행하라.'},
                    ],
                }],
            )
            text = resp.content[0].text
            usage = {
                'input_tokens': resp.usage.input_tokens,
                'output_tokens': resp.usage.output_tokens,
            }
            return text, usage
        except (anthropic.RateLimitError, anthropic.APIStatusError) as e:
            last_err = e
            wait = 2 ** attempt * 5
            print(f'    retry {attempt+1}/{retries} after {wait}s: {e}', file=sys.stderr)
            time.sleep(wait)
        except Exception as e:
            last_err = e
            print(f'    error: {e}', file=sys.stderr)
            break
    raise RuntimeError(f'failed after {retries} retries: {last_err}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--article', '-a', required=True)
    ap.add_argument('--unit', '-u', help='single unit id (default: all)')
    ap.add_argument('--model', '-m', default='claude-sonnet-4-6',
                    choices=list(MODEL_TO_TAG.keys()))
    ap.add_argument('--engine-tag', help='override output folder name')
    ap.add_argument('--force', action='store_true', help='overwrite existing')
    args = ap.parse_args()

    art_dir = resolve_article_dir(args.article)
    meta = yaml.safe_load((art_dir / 'meta.yaml').read_text(encoding='utf-8'))
    units = meta.get('units', [])
    if not units:
        print(f'! no units in meta.yaml of {art_dir.name}'); sys.exit(1)

    tag = args.engine_tag or MODEL_TO_TAG[args.model]
    out_dir = art_dir / 'ocr' / tag
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.unit:
        units = [u for u in units if u['id'] == args.unit]
        if not units:
            print(f'! unit {args.unit} not found'); sys.exit(1)

    client = anthropic.Anthropic(api_key=KEY)
    print(f'(article: {art_dir.name} | model: {args.model} | tag: {tag} | units: {len(units)})')
    total_in = 0
    total_out = 0
    for u in units:
        out_path = out_dir / f"{u['id']}.txt"
        img_path = art_dir / u['file']
        if out_path.exists() and not args.force:
            print(f'  skip {u["id"]} (exists)')
            continue
        if not img_path.exists():
            print(f'  ! missing image: {img_path}')
            continue
        try:
            t0 = time.time()
            text, usage = call_anthropic(client, args.model, img_path)
            elapsed = time.time() - t0
            header = (
                f"# {args.model} via Anthropic API — vision OCR (2026-05-09)\n"
                f"# Source: {art_dir.name}/{u['file']}\n"
                f"# Tokens: in={usage['input_tokens']} out={usage['output_tokens']} elapsed={elapsed:.1f}s\n\n"
            )
            out_path.write_text(header + text, encoding='utf-8')
            total_in += usage['input_tokens']
            total_out += usage['output_tokens']
            print(f'  OK {u["id"]} ({usage["input_tokens"]}+{usage["output_tokens"]} tok, {elapsed:.1f}s)')
        except Exception as e:
            print(f'  FAIL {u["id"]}: {e}')
    print(f'\n== total tokens: in={total_in} out={total_out}')
    if 'sonnet' in args.model:
        cost = total_in * 3e-6 + total_out * 15e-6
    else:
        cost = total_in * 15e-6 + total_out * 75e-6
    print(f'== est cost: ~${cost:.4f}')


if __name__ == '__main__':
    main()
