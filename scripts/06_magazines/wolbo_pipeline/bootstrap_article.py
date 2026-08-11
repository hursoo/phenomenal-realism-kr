"""C2 진입 도구: series_index 기반 article 폴더 skeleton 생성. v1.0 (2026-05-09)

각 article에 대해:
  - articles/<NN>_<slug>_<YYYY-MM>/ 폴더 생성
  - 빈 하위: units/, ocr/{claude_opus_4_7,gemini,paddle}/, transcripts/
  - meta.yaml skeleton 작성 (출처·SHA256·픽셀 픽업 자동, layout·units는 placeholder)

slug 규칙: title의 첫 2자 한자 (충돌은 YYYY-MM 차이로 폴더명 단위에서 해소).

기존 #1(01_kwonyu_1911-01) 및 #10(samples/oldhangul_sample_wolbo18)은 건너뜀.

Usage:
    python bootstrap_article.py --series 2          # 단일 series_index
    python bootstrap_article.py --series 2-9        # 범위
    python bootstrap_article.py --all               # 전체 (기존 #1·#10 제외)
    python bootstrap_article.py --series 2 --dry-run  # 검토만 (파일 안 만듦)
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import sys
from pathlib import Path

from PIL import Image

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

BASE = Path(r'C:/hp_data/0_tnt/hyeonsang/_ocr_experiments/cheondogyo_wolbo_series')
RAW_ARTICLES = Path(r'C:/hp_data/0_tnt/hyeonsang/raw/journals/cheondogyo_wolbo/nl_bibliography/articles')
SERIES_INDEX = BASE / 'series_index.csv'

# 기존 article은 다른 명명 규칙(romanized) 또는 sample 위치이므로 제외
SKIP_SERIES = {1, 10}


def is_hanja(c: str) -> bool:
    return 0x3400 <= ord(c) <= 0x9FFF


def first_hanja_slug(title: str, n: int = 2) -> str:
    chars = [c for c in title if is_hanja(c)]
    return ''.join(chars[:n]) if chars else 'NOSLUG'


def parse_range(arg: str) -> list[int]:
    """'2', '2-9', '2,5,10' → list of ints."""
    out = []
    for part in arg.split(','):
        if '-' in part:
            a, b = part.split('-', 1)
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return sorted(set(out))


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def img_size(p: Path) -> tuple[int, int]:
    with Image.open(p) as im:
        return im.size  # (w, h)


def load_series_rows() -> list[dict]:
    with SERIES_INDEX.open(encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def build_meta_yaml(row: dict, slug: str, source_pages: list[dict], folder_name: str) -> str:
    """Skeleton meta.yaml content. layout·units는 placeholder.

    cnts_id가 빈 값이면 (수동 발굴) source_url·source_dir·cnts_id를 적절히 처리.
    """
    cnts_id = (row.get('cnts_id') or '').strip()
    has_cnts = bool(cnts_id)
    cnts_field = cnts_id if has_cnts else 'null  # 수동 발굴, CNTS-ID 미수집'
    source_url_field = (
        f'https://www.nl.go.kr/NL/contents/search.do?viewKey={cnts_id}&viewType=C&category=기사'
        if has_cnts else 'null  # CNTS-ID 미수집 (NL 직접 검색으로 수동 발굴)'
    )
    source_dir_field = (
        f'hyeonsang/raw/journals/cheondogyo_wolbo/nl_bibliography/articles/{cnts_id}/'
        if has_cnts else f'hyeonsang/raw/journals/cheondogyo_wolbo/nl_bibliography/articles/{folder_name}/'
    )
    lines = [
        f'# Skeleton meta — series_index #{row["series_index"]}, generated {2026}-05-09 by bootstrap_article.py',
        '# layout·units는 시각 검증 후 채울 것 (TODO 표시 영역)',
        '',
        'article:',
        f'  series_index: {row["series_index"]}',
        f'  slug: {slug}_{row["publish_date"][:7]}',
        f'  cnts_id: {cnts_field}',
        f'  title: {row["title"]}',
        f'  author: 李敦化',
        f'  journal: 천도교회월보 (天道敎會月報)',
        f'  issue_total: {row["tonggwon"]}',
        f'  publication_date: {row["publish_date"]}',
        f'  section: {row["section"]}',
        f'  page_in_journal: {row["page_in_journal"]}',
        f'  partial_download: {"true" if row.get("partial") == "Y" else "false"}',
        f'  source_url: {source_url_field}',
        '',
        'source_pages:',
    ]
    for sp in source_pages:
        lines.append(f'  - file: {sp["file"]}')
        lines.append(f'    sha256: {sp["sha256"]}')
        lines.append(f'    bytes: {sp["bytes"]}')
        lines.append(f'    pixels: {sp["pixels"]}')
    lines.append(f'source_dir: {source_dir_field}')
    lines.extend([
        '',
        '# ========== TODO (Soo 시각 검증 후 채움) ==========',
        '',
        'layout:',
        '  page_orientation: vertical_writing',
        '  bands_per_page: 2  # TODO: 시각 검증',
        '  divider_kind: thin_wavy_line  # TODO: thin_wavy_line / vertical_wavy_split / etc',
        '  divider_y: TODO  # 가로 분리선 y좌표 (없으면 null)',
        '  layout_type: TODO  # horizontal_only(L1) / vertical_wavy_split(L2) / mixed',
        '  reading_order: snake  # TODO: snake / 별도',
        '  body_left_margin: 80  # 부속 영역 제외 기본값',
        '  hanja_ratio_estimate: TODO  # ~0.65 / ~0.80 등',
        '  oldhangul_density: TODO  # very_low / low / mid / high',
        '',
        'units: []  # TODO: 시각 검증 후 [{id, file, page, crop, pixels, role, contains}, ...]',
        '',
        'excluded: []  # TODO: 본 기사 외 영역 (다른 기사 꼬리 등)',
        '',
        'ancillary:',
        '  section_label: ' + row['section'],
        '  page_numbers: []  # TODO: 페이지번호 한자 (二五 등)',
        '',
        'processing_state:',
        '  phase_2_1_unit_extraction: pending',
        '  phase_3_ocr: pending',
        '  phase_4_consensus_and_correction: pending',
        '  phase_5_high_fidelity_transcript: pending',
        '  phase_6_modern_reading_version: pending',
        '',
        'policy_refs:',
        '  series_design: _design/2026-05-08_journal_intermediation_v01.md',
        '  consensus_policy: _design/2026-05-09_cheondogyo_wolbo_consensus_policy_v0_3.md',
        '  series_index: hyeonsang/_ocr_experiments/cheondogyo_wolbo_series/series_index.csv',
    ])
    return '\n'.join(lines) + '\n'


def bootstrap_one(row: dict, dry_run: bool) -> Path | None:
    series_n = int(row['series_index'])
    cnts_id = (row.get('cnts_id') or '').strip()

    # 출처 페이지 디렉토리 결정 — CNTS-ID 기반 OR fallback (시리즈 번호 + YYYY-MM)
    if cnts_id:
        src_dir = RAW_ARTICLES / cnts_id
        slug = first_hanja_slug(row['title'])
        folder_name = f'{series_n:02d}_{slug}_{row["publish_date"][:7]}'
    else:
        # fallback: 수동 발굴분. raw 폴더명은 {NN:02d}_<slug>_<YYYY-MM> 형식.
        yyyy_mm = row['publish_date'][:7]
        prefix = f'{series_n:02d}_'
        candidates = [d for d in RAW_ARTICLES.iterdir() if d.is_dir() and d.name.startswith(prefix) and d.name.endswith(yyyy_mm)]
        if not candidates:
            print(f'  ⚠ #{series_n}: no raw folder matching {prefix}*_{yyyy_mm}', file=sys.stderr)
            return None
        if len(candidates) > 1:
            print(f'  ⚠ #{series_n}: multiple raw folders: {[c.name for c in candidates]}', file=sys.stderr)
            return None
        src_dir = candidates[0]
        folder_name = src_dir.name  # raw 폴더명을 작업 폴더명으로 그대로 사용
        # slug = folder의 두 번째 segment (예: 76_東經_1912-08 → 東經)
        parts = folder_name.split('_')
        slug = parts[1] if len(parts) >= 3 else first_hanja_slug(row['title'])

    article_dir = BASE / 'articles' / folder_name

    if not src_dir.exists():
        print(f'  ⚠ #{series_n}: source dir not found at {src_dir}', file=sys.stderr)
        return None
    page_files = sorted(p for p in src_dir.iterdir() if p.suffix.lower() in {'.jpg', '.jpeg', '.png'} and p.name.startswith('page_'))
    if not page_files:
        print(f'  ⚠ #{series_n}: no page_*.jpg in {src_dir}', file=sys.stderr)
        return None

    source_pages = []
    for pf in page_files:
        w, h = img_size(pf)
        source_pages.append({
            'file': pf.name,
            'sha256': sha256_file(pf),
            'bytes': pf.stat().st_size,
            'pixels': f'{w}x{h}',
        })

    print(f'  #{series_n}: {folder_name} ({len(source_pages)} pages)')
    if dry_run:
        return article_dir

    if article_dir.exists():
        print(f'    skip (folder already exists)')
        return article_dir

    # 폴더 구조
    article_dir.mkdir(parents=True)
    (article_dir / 'units').mkdir()
    (article_dir / 'ocr' / 'claude_opus_4_7').mkdir(parents=True)
    (article_dir / 'ocr' / 'gemini').mkdir(parents=True)
    (article_dir / 'ocr' / 'paddle').mkdir(parents=True)
    (article_dir / 'transcripts').mkdir()

    # meta.yaml
    meta_text = build_meta_yaml(row, slug, source_pages, folder_name)
    (article_dir / 'meta.yaml').write_text(meta_text, encoding='utf-8')
    print(f'    created folder + meta.yaml skeleton')
    return article_dir


def main() -> int:
    ap = argparse.ArgumentParser(description='C2 article folder bootstrap v1.0')
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--series', '-s', help='series_index (e.g. "2", "2-9", "2,5,10")')
    g.add_argument('--all', action='store_true', help='all 75 articles (skips #1, #10)')
    ap.add_argument('--dry-run', action='store_true', help='print plan only, do not create files')
    args = ap.parse_args()

    rows = load_series_rows()
    if args.all:
        targets = [r for r in rows if int(r['series_index']) not in SKIP_SERIES]
    else:
        wanted = set(parse_range(args.series))
        targets = [r for r in rows if int(r['series_index']) in wanted and int(r['series_index']) not in SKIP_SERIES]
        skipped_in_range = [r for r in rows if int(r['series_index']) in wanted and int(r['series_index']) in SKIP_SERIES]
        for r in skipped_in_range:
            print(f'  skip #{r["series_index"]} (already exists in different naming/location)')

    print(f'Bootstrapping {len(targets)} articles{" (DRY RUN)" if args.dry_run else ""}\n')
    created = 0
    for r in targets:
        if bootstrap_one(r, args.dry_run):
            created += 1
    print(f'\nDone. {created}/{len(targets)} articles processed.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
