"""C1: 75편 시간순 정렬 + series_index 부여. v1.0 (2026-05-09)

입력: hyeonsang/raw/journals/cheondogyo_wolbo/nl_bibliography/out/yid_99_with_downloads.csv
출력:
  - series_index.csv : 다운로드 완료 75편 발행일 순 정렬 + series_index 1~75
  - series_index.md  : 인간 검토용 마크다운 표

C2 (단 분리)에서 본 인덱스를 기준으로 article 폴더(`articles/<NN>_<slug>_<YYYY-MM>/`) 생성.
slug는 한자 표제 첫 2~3자 또는 음역 (수기 결정 — 자동 생성 보류).
"""
from __future__ import annotations
import csv
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r'C:/hp_data/0_tnt/hyeonsang/_ocr_experiments/cheondogyo_wolbo_series')
SRC = Path(r'C:/hp_data/0_tnt/hyeonsang/raw/journals/cheondogyo_wolbo/nl_bibliography/out/yid_99_with_downloads.csv')

# 다운로드 상태 표시 (● 전체, ◐ 부분)
DOWNLOADED_STATUSES = {'●', '◐'}


def parse_date(s: str) -> tuple[int, int, int]:
    """YYYY-MM-DD → (year, month, day) for sorting."""
    parts = s.split('-')
    return (int(parts[0]), int(parts[1]), int(parts[2])) if len(parts) == 3 else (0, 0, 0)


def main() -> int:
    rows = []
    with SRC.open(encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['status'] in DOWNLOADED_STATUSES:
                rows.append(row)

    # 발행일 → 통권(보조 키)으로 정렬
    rows.sort(key=lambda r: (parse_date(r['publish_date']), int(r.get('tonggwon', '0') or '0')))

    # series_index 1..N 부여
    out_rows = []
    for i, r in enumerate(rows, 1):
        out_rows.append({
            'series_index': i,
            'publish_date': r['publish_date'],
            'tonggwon': r['tonggwon'],
            'section': r['section'],
            'title': r['title'],
            'page_in_journal': r['page'],
            'n_pages_journal_total': r['n_pages_meta'],
            'cnts_id': r['nl_cnts_id'],
            'downloaded_pages': r['downloaded_pages'],
            'downloaded_bytes': r['downloaded_bytes'],
            'partial': 'Y' if r['status'] == '◐' else 'N',
        })

    # CSV 산출
    csv_out = BASE / 'series_index.csv'
    with csv_out.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        writer.writeheader()
        writer.writerows(out_rows)
    print(f'wrote {csv_out} ({len(out_rows)} rows)')

    # md 산출 (인간 검토용)
    last_date = out_rows[-1]['publish_date']
    md_lines = [
        '# 천도교회월보 이돈화 시리즈 인덱스 (C1, 2026-05-09)',
        '',
        f'**원본**: `hyeonsang/raw/journals/cheondogyo_wolbo/nl_bibliography/out/yid_99_with_downloads.csv` (99건 中 다운로드 75편).',
        '',
        f'**발행일 + 통권 순 정렬**, series_index 1~{len(out_rows)} 부여. C2 (단 분리) 진입 기준 인덱스.',
        '',
        f'**부분 다운로드(◐)** 표시: 페이지 일부만 확보 — 실제 본문 충분 여부는 article 폴더 생성 시 검증.',
        '',
        f'## 시기 cutoff 제약',
        '',
        f'본 매개층 cutoff는 **1911-01-15 ~ 1922-05-15** (75편). 설계 cutoff인 1924까지 사이에 ~2년 공백 발생. 원인: NL(국립중앙도서관) 디지털 원문 미제공 (1922-10·1923-08×2·1923-10·1924-04·1924-10 — 6건 ✗ 또는 □). 1924년 (3) 단행본 직전 매개층 데이터가 끊기는 한계는 분석에서 명시.',
        '',
        '## 표',
        '',
        '| # | 발행일 | 통권 | 섹션 | 제목 | 본문 시작p | 다운p | CNTS-ID |',
        '|---:|---|---:|---|---|---:|---:|---|',
    ]
    for r in out_rows:
        partial_mark = ' (◐)' if r['partial'] == 'Y' else ''
        md_lines.append(
            f"| {r['series_index']} | {r['publish_date']} | {r['tonggwon']} | {r['section']} | {r['title']}{partial_mark} | {r['page_in_journal']} | {r['downloaded_pages']} | {r['cnts_id']} |"
        )

    md_out = BASE / 'series_index.md'
    md_out.write_text('\n'.join(md_lines) + '\n', encoding='utf-8')
    print(f'wrote {md_out}')

    # 본 1편(article 01) 정합성 확인
    art01_cnts = 'CNTS-00048033199'
    art01 = next((r for r in out_rows if r['cnts_id'] == art01_cnts), None)
    if art01:
        print(f"\n본 1편 정합: series_index={art01['series_index']}, 발행일={art01['publish_date']}, 통권={art01['tonggwon']}")
        if art01['series_index'] == 1:
            print('  ✓ 기존 articles/01_kwonyu_1911-01/ 와 series_index=1 일치')
        else:
            print(f"  ⚠ 기존 articles/01_… 와 다름 — 기존 폴더 series_index를 {art01['series_index']}로 갱신 필요 여부 확인")

    # 부 표본(sample)도 정합성 확인
    sample_cnts = 'CNTS-00048061346'
    sample = next((r for r in out_rows if r['cnts_id'] == sample_cnts), None)
    if sample:
        print(f"부 표본 정합: series_index={sample['series_index']}, 발행일={sample['publish_date']}, 통권={sample['tonggwon']}")
        print(f"  → samples/oldhangul_sample_wolbo18/ 의 시리즈 위치는 #{sample['series_index']}")

    # 첫·마지막
    print(f"\n범위: series_index 1 ({out_rows[0]['publish_date']}, {out_rows[0]['title']}) ~ {len(out_rows)} ({out_rows[-1]['publish_date']}, {out_rows[-1]['title']})")
    return 0


if __name__ == '__main__':
    sys.exit(main())
