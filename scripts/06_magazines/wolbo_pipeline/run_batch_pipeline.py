"""Multi-article batch orchestrator. v1.0 (2026-05-09)

series_index.csv 기반 64편 무인 일괄 처리:
  cut_units → run_gemini_ocr → run_paddle_ocr → run_claude_ocr (Opus) → consensus review + draft

각 단계 idempotent (결과 있으면 skip). 실패 article은 failures.txt에 기록 후 다음 진행.
진행 상황을 batch.log에 append. 완료 시 summary 출력.

Usage:
    python run_batch_pipeline.py                        # 전 article (이미 완료된 것 자동 skip)
    python run_batch_pipeline.py --skip-claude          # Claude만 제외 (Gemini+Paddle만)
    python run_batch_pipeline.py --only 3-29            # series 3-29만
    python run_batch_pipeline.py --claude-model claude-opus-4-7

Resume-safe: 중간에 죽어도 다시 실행하면 done인 것 자동 skip.
"""
from __future__ import annotations
import argparse
import csv
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

BASE = Path(r'C:/hp_data/0_tnt/hyeonsang/_ocr_experiments/cheondogyo_wolbo_series')
SCRIPTS = BASE / 'scripts'
LOG_PATH = Path(r'C:/hp_data/0_tnt/_batch.log')
FAIL_PATH = Path(r'C:/hp_data/0_tnt/_batch_failures.txt')

# series_index numbers to skip entirely (already fully done in 5표본 + 본 1·2편 + sample folder)
ALWAYS_SKIP = {1, 2, 10}  # #1·#2 본편, #10 sample (oldhangul_sample_wolbo18)


def log(msg: str):
    line = f'[{datetime.now().strftime("%H:%M:%S")}] {msg}'
    print(line, flush=True)
    with LOG_PATH.open('a', encoding='utf-8') as f:
        f.write(line + '\n')


def run_script(script: str, *args: str, timeout: int = 1800) -> tuple[bool, str]:
    cmd = [sys.executable, str(SCRIPTS / script), *args]
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=timeout,
        )
        return r.returncode == 0, (r.stdout or '') + (r.stderr or '')
    except subprocess.TimeoutExpired:
        return False, f'TIMEOUT after {timeout}s'
    except Exception as e:
        return False, f'EXCEPTION: {e}'


def find_article_dir(series_index: int) -> Path | None:
    matches = list((BASE / 'articles').glob(f'{series_index:02d}_*'))
    return matches[0] if matches else None


def is_step_done(art_dir: Path, step: str) -> bool:
    """Check whether a step is already completed for an article."""
    if step == 'cut':
        return any((art_dir / 'units').glob('*.png'))
    if step == 'gemini':
        d = art_dir / 'ocr' / 'gemini'
        if not d.exists():
            return False
        units_dir = art_dir / 'units'
        unit_files = list(units_dir.glob('*.png'))
        ocr_files = list(d.glob('*.txt'))
        return len(ocr_files) >= len(unit_files) and len(unit_files) > 0
    if step == 'paddle':
        d = art_dir / 'ocr' / 'paddle'
        if not d.exists():
            return False
        unit_files = list((art_dir / 'units').glob('*.png'))
        ocr_files = list(d.glob('*.txt'))
        return len(ocr_files) >= len(unit_files) and len(unit_files) > 0
    if step == 'claude':
        d = art_dir / 'ocr' / 'claude_opus_4_7'
        if not d.exists():
            return False
        unit_files = list((art_dir / 'units').glob('*.png'))
        ocr_files = list(d.glob('*.txt'))
        return len(ocr_files) >= len(unit_files) and len(unit_files) > 0
    if step == 'consensus':
        d = art_dir / 'transcripts'
        return any(d.glob('*.high_fidelity.draft_v0.md')) if d.exists() else False
    return False


def process_article(series_index: int, art_dir: Path, args) -> dict:
    slug = art_dir.name
    log(f'-- #{series_index} {slug} --')
    result = {'slug': slug, 'series_index': series_index, 'steps': {}, 'errors': []}

    if not is_step_done(art_dir, 'cut'):
        log(f'   cut_units...')
        ok, out = run_script('cut_units.py', '--article', slug, timeout=120)
        result['steps']['cut'] = ok
        if not ok:
            result['errors'].append(f'cut: {out[-200:]}')
            log(f'   cut FAIL')
            return result
    else:
        result['steps']['cut'] = 'skip'

    if not args.skip_gemini and not is_step_done(art_dir, 'gemini'):
        log(f'   run_gemini_ocr...')
        ok, out = run_script('run_gemini_ocr.py', '--article', slug, timeout=900)
        result['steps']['gemini'] = ok
        if not ok:
            result['errors'].append(f'gemini: {out[-200:]}')
    else:
        result['steps']['gemini'] = 'skip'

    if not args.skip_paddle and not is_step_done(art_dir, 'paddle'):
        log(f'   run_paddle_ocr...')
        ok, out = run_script('run_paddle_ocr.py', '--article', slug, timeout=900)
        result['steps']['paddle'] = ok
        if not ok:
            result['errors'].append(f'paddle: {out[-200:]}')
    else:
        result['steps']['paddle'] = 'skip'

    if not args.skip_claude and not is_step_done(art_dir, 'claude'):
        log(f'   run_claude_ocr (Opus)...')
        ok, out = run_script(
            'run_claude_ocr.py',
            '--article', slug,
            '--model', args.claude_model,
            timeout=1800,
        )
        result['steps']['claude'] = ok
        if not ok:
            result['errors'].append(f'claude: {out[-200:]}')
            log(f'   claude FAIL: {out[-100:]}')
    else:
        result['steps']['claude'] = 'skip'

    if not is_step_done(art_dir, 'consensus'):
        log(f'   consensus review + draft...')
        ok1, out1 = run_script('consensus.py', 'review', '--article', slug, timeout=300)
        ok2, out2 = run_script('consensus.py', 'draft', '--article', slug, timeout=300)
        result['steps']['consensus'] = ok1 and ok2
        if not (ok1 and ok2):
            result['errors'].append(f'consensus: review_ok={ok1} draft_ok={ok2}')
    else:
        result['steps']['consensus'] = 'skip'

    if result['errors']:
        with FAIL_PATH.open('a', encoding='utf-8') as f:
            f.write(f'#{series_index} {slug}\n')
            for e in result['errors']:
                f.write(f'  {e}\n')

    log(f'   done #{series_index}: {result["steps"]}')
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', help='range like 3-29 or single 30')
    ap.add_argument('--skip', default='', help='comma-separated series_index to skip')
    ap.add_argument('--skip-claude', action='store_true')
    ap.add_argument('--skip-gemini', action='store_true')
    ap.add_argument('--skip-paddle', action='store_true')
    ap.add_argument('--claude-model', default='claude-opus-4-7',
                    choices=['claude-opus-4-7', 'claude-sonnet-4-6', 'claude-haiku-4-5-20251001'])
    args = ap.parse_args()

    user_skip = set(int(x) for x in args.skip.split(',') if x.strip())
    skip_set = ALWAYS_SKIP | user_skip

    if args.only:
        if '-' in args.only:
            lo, hi = args.only.split('-')
            target_range = list(range(int(lo), int(hi) + 1))
        else:
            target_range = [int(args.only)]
    else:
        target_range = list(range(1, 76))

    # Read series_index for ordering
    series = {}
    with (BASE / 'series_index.csv').open(encoding='utf-8') as f:
        for row in csv.DictReader(f):
            series[int(row['series_index'])] = row

    log(f'=== batch_pipeline start (claude_model={args.claude_model}, range={target_range[0]}-{target_range[-1]}) ===')
    t0 = time.time()
    results = []
    for n in target_range:
        if n in skip_set:
            log(f'-- #{n}: ALWAYS_SKIP')
            continue
        if n not in series:
            log(f'-- #{n}: not in series_index')
            continue
        art_dir = find_article_dir(n)
        if art_dir is None:
            log(f'-- #{n}: no folder')
            continue
        try:
            r = process_article(n, art_dir, args)
            results.append(r)
        except Exception as e:
            log(f'-- #{n}: EXCEPTION {e}')
            with FAIL_PATH.open('a', encoding='utf-8') as f:
                f.write(f'#{n} EXCEPTION: {e}\n')

    elapsed = time.time() - t0
    n_done = len(results)
    n_fail = sum(1 for r in results if r['errors'])
    log(f'=== done in {elapsed/60:.1f} min, {n_done} processed, {n_fail} with errors ===')


if __name__ == '__main__':
    main()
