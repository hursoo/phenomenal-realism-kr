"""Batch 마무리 — meta.yaml processing_state 갱신 + ⚠️ 마커 통계 산출. v1.0 (2026-05-10)

각 article의 transcripts/<slug>.high_fidelity.draft_v0.md를 분석하여:
  - ⚠️ 마커 수 카운트
  - meta.yaml processing_state 갱신 (phase_3·4 = completed_2엔진)
  - post_ocr_findings 자리에 batch 메타 정보 추가

Usage:
    python finalize_batch.py            # 모든 article (이미 done인 것은 skip)
    python finalize_batch.py --only 3-29
"""
from __future__ import annotations
import argparse
import csv
import re
import sys
from pathlib import Path
import yaml

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

BASE = Path(r'C:/hp_data/0_tnt/hyeonsang/_ocr_experiments/cheondogyo_wolbo_series')


def count_warnings(draft_path: Path) -> int:
    if not draft_path.exists():
        return -1
    text = draft_path.read_text(encoding='utf-8')
    return len(re.findall(r'⚠️', text))


def update_meta(art_dir: Path, warnings: int, n_units: int) -> bool:
    meta_path = art_dir / 'meta.yaml'
    text = meta_path.read_text(encoding='utf-8')
    meta = yaml.safe_load(text)
    state = meta.setdefault('processing_state', {})
    # Skip if already finalized in 5표본 (has post_ocr_findings)
    if 'post_ocr_findings' in meta and 'phase_4_consensus_and_correction' in state and 'draft_v0' in str(state.get('phase_4_consensus_and_correction', '')):
        # Already finalized (5표본). Don't overwrite.
        return False

    # Detect engine availability
    ocr_root = art_dir / 'ocr'
    units_dir = art_dir / 'units'
    n_units_actual = len(list(units_dir.glob('*.png')))
    cl = len(list((ocr_root / 'claude_opus_4_7').glob('*.txt'))) if (ocr_root / 'claude_opus_4_7').exists() else 0
    gm = len(list((ocr_root / 'gemini').glob('*.txt'))) if (ocr_root / 'gemini').exists() else 0
    pd = len(list((ocr_root / 'paddle').glob('*.txt'))) if (ocr_root / 'paddle').exists() else 0

    engines = []
    if cl >= n_units_actual: engines.append('Claude_Opus_4.7')
    if gm >= n_units_actual: engines.append('Gemini_2.5_Pro')
    if pd >= n_units_actual: engines.append('Paddle')
    eng_str = '+'.join(engines)
    eng_n = len(engines)
    state['phase_3_ocr'] = f'completed_{eng_n}engine_2026-05-10 ({eng_str})'
    state['phase_4_consensus_and_correction'] = f'draft_v0_auto_2026-05-10 (warnings={warnings}, human_mediation_pending)'
    if 'phase_5_high_fidelity_transcript' not in state:
        state['phase_5_high_fidelity_transcript'] = 'pending'
    if 'phase_6_modern_reading_version' not in state:
        state['phase_6_modern_reading_version'] = 'pending'

    new_text = yaml.dump(meta, allow_unicode=True, sort_keys=False, default_flow_style=False)
    meta_path.write_text(new_text, encoding='utf-8')
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', help='range like 3-29')
    args = ap.parse_args()
    if args.only:
        if '-' in args.only:
            lo, hi = args.only.split('-')
            target = list(range(int(lo), int(hi)+1))
        else:
            target = [int(args.only)]
    else:
        target = list(range(1, 76))

    rows = []
    for n in target:
        matches = list((BASE / 'articles').glob(f'{n:02d}_*'))
        if not matches:
            continue
        art_dir = matches[0]
        slug = art_dir.name
        draft = list((art_dir / 'transcripts').glob('*.high_fidelity.draft_v0.md'))
        if not draft:
            print(f'  #{n} {slug}: NO draft_v0')
            continue
        w = count_warnings(draft[0])
        n_units = len(list((art_dir / 'units').glob('*.png')))
        updated = update_meta(art_dir, w, n_units)
        rows.append((n, slug, n_units, w, 'updated' if updated else 'kept(5표본)'))
        print(f'  #{n:>2} {slug}: units={n_units} warnings={w} ({rows[-1][4]})')

    print(f'\n=== summary ===')
    print(f'total articles: {len(rows)}')
    total_w = sum(r[3] for r in rows if r[3] >= 0)
    total_u = sum(r[2] for r in rows)
    print(f'total units: {total_u}')
    print(f'total warnings: {total_w}')
    print(f'avg warnings per unit: {total_w/total_u:.1f}' if total_u else 'n/a')

    # Save summary CSV
    summary_path = BASE / 'batch_2026-05-10_summary.csv'
    with summary_path.open('w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['series_index', 'slug', 'units', 'warnings', 'meta_status'])
        w.writerows(rows)
    print(f'summary saved: {summary_path}')


if __name__ == '__main__':
    main()
