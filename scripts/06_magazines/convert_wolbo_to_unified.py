"""천도교회월보 draft_v0/v1 → 통일 row-level xlsx 변환.

입력: cheondogyo_wolbo_series/articles/<NN_slug_YYYY-MM>/transcripts/
       - draft_v1 우선: <slug>.high_fidelity.md (인간 검수 완료, ⚠️ 마커 없음)
       - draft_v0 fallback: <slug>.high_fidelity.draft_v0.md (⚠️ 마커 안 [C:...] Claude OCR 본 추출)

출력: MA_YD_10-20_WB.xlsx

처리:
1. series_index.csv를 발행일 순으로 정렬 → C 번호 = series_index
2. articles/ 폴더 스캔 (#10 sample 제외)
3. 본문 추출 (frontmatter + [body] 분리, draft_v0는 ⚠️ 마커 처리)
4. 문장 분리 + N 묶음
5. local_id 부여: C##-S00-I00-P00-S## (단락 정보 없음, P00 일관)
6. n_chunk_id: 한 글 안 모든 문장을 모아 n=5 비중첩 묶음
"""
import argparse
import csv
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

import openpyxl

sys.stdout.reconfigure(encoding='utf-8')

WOLBO_BASE = Path(r'C:\hp_data\0_workspaces\0_tnt\hyeonsang\_ocr_experiments\cheondogyo_wolbo_series')
ARTICLES_DIR = WOLBO_BASE / 'articles'
SAMPLES_DIR = WOLBO_BASE / 'samples'
SERIES_INDEX = WOLBO_BASE / 'series_index.csv'
OUT_DIR = Path(r'C:\hp_data\0_workspaces\0_tnt\hyeonsang\_ocr_experiments\unified_db_2026-05-19\output')

DB_ID = 'MA_YD_10-20_WB'

N = 5
MERGE_THRESHOLD = 3

# 2026-05-19: 모집단 160편 — #10은 samples/oldhangul_sample_wolbo18/에서 처리
SKIP_SERIES: set = set()  # 모두 포함
SAMPLE_MAP = {10: 'oldhangul_sample_wolbo18'}  # series_n → samples/ 하위 폴더명

ENDING_PATTERNS = [
    r'ᄒᆞᆯ지어다', r'ᄒᆞ지어다', r'ᄒᆞᆯ진뎌', r'ᄒᆞᆯ지라',
    r'ᄒᆞᄂᆞ니라', r'ᄒᆞ니라', r'ᄒᆞ리오', r'ᄒᆞ리라',
    r'ᄒᆞ도다', r'ᄒᆞ더라',
    r'노라', r'도다', r'더라', r'리오', r'리라', r'지어다', r'진뎌',
    r'\.', r'。', r'!', r'\?',
]
SPLIT_PATTERN = re.compile('(' + '|'.join(ENDING_PATTERNS) + ')')
HANJA = re.compile(r'[一-鿿]')

MARKER = re.compile(r'⚠️\[C:(.*?)\|G:.*?\]', re.DOTALL)
FRONTMATTER = re.compile(r'^---\n.*?\n---\n', re.DOTALL)


def split_sentences(text: str) -> list:
    if not text:
        return []
    parts = SPLIT_PATTERN.split(text)
    sentences = []
    buf = ''
    for i, p in enumerate(parts):
        if i % 2 == 0:
            buf += p
        else:
            buf += p
            if buf.strip() and HANJA.search(buf):
                sentences.append(buf.strip())
            buf = ''
    if buf.strip() and HANJA.search(buf):
        sentences.append(buf.strip())
    return sentences


def extract_claude_base(text: str) -> str:
    """draft_v0의 ⚠️ 마커 안 [C:...] Claude OCR 본만."""
    return MARKER.sub(lambda m: m.group(1).replace('∅', ''), text)


def strip_to_body(text: str) -> str:
    """yaml frontmatter + 헤더 마커 제거하고 본문만."""
    text = FRONTMATTER.sub('', text)
    if '[body]' in text:
        text = text.split('[body]', 1)[1]
    # 본문은 첫 ## 헤더 전까지로 한정 (## v0→v1, ## 다음 단계 등 부수 섹션 제거)
    parts = text.split('\n## ', 1)
    return parts[0]


def assign_n_chunks(sentence_count: int) -> list:
    chunks = [list(range(i, min(i+N, sentence_count))) for i in range(0, sentence_count, N)]
    if len(chunks) >= 2 and len(chunks[-1]) < MERGE_THRESHOLD:
        chunks[-2].extend(chunks[-1])
        chunks.pop()
    result = [0] * sentence_count
    for n_idx, chunk in enumerate(chunks, start=1):
        for sent_idx in chunk:
            result[sent_idx] = n_idx
    return result


def find_article_folder(series_n: int) -> Path | None:
    matches = list(ARTICLES_DIR.glob(f'{series_n:02d}_*'))
    if matches:
        return matches[0]
    # fallback: samples/ 폴더 (예: #10)
    if series_n in SAMPLE_MAP:
        sample_path = SAMPLES_DIR / SAMPLE_MAP[series_n]
        if sample_path.exists():
            return sample_path
    return None


def load_transcript(folder: Path) -> tuple:
    """draft_v1 우선, draft_v0 fallback. unit별 분리 transcript도 처리. (body_text, version)"""
    transcripts = folder / 'transcripts'
    if not transcripts.is_dir():
        return None
    # 통상 — full article transcript
    v1_files = [f for f in transcripts.iterdir() if f.name.endswith('.high_fidelity.md') and 'draft_v0' not in f.name and not f.name.startswith('unit_')]
    v0_files = [f for f in transcripts.iterdir() if f.name.endswith('.high_fidelity.draft_v0.md')]
    if v1_files:
        text = v1_files[0].read_text(encoding='utf-8')
        return strip_to_body(text), 'v1'
    if v0_files:
        text = v0_files[0].read_text(encoding='utf-8')
        body = strip_to_body(text)
        body = extract_claude_base(body)
        return body, 'v0_claude_base'
    # fallback: unit_*.high_fidelity.md (예: #10 sample)
    unit_v1_files = sorted([f for f in transcripts.iterdir() if f.name.startswith('unit_') and f.name.endswith('.high_fidelity.md')])
    if unit_v1_files:
        bodies = []
        for f in unit_v1_files:
            text = f.read_text(encoding='utf-8')
            bodies.append(strip_to_body(text))
        return '\n'.join(bodies), 'v1_unit_partial'
    return None


def process_one_article(series_n: int, manifest_row: dict) -> list:
    folder = find_article_folder(series_n)
    if folder is None:
        return None
    result = load_transcript(folder)
    if result is None:
        return None
    body_text, version = result
    body_text = unicodedata.normalize('NFC', body_text)

    sentences = split_sentences(body_text)
    if not sentences:
        return None

    # N 묶음 부여
    n_assignments = assign_n_chunks(len(sentences))

    # row 생성
    c_str = f'C{series_n:02d}'
    s_str = 'S00'
    i_str = 'I00'
    p_str = 'P00'  # 단락 식별 없음

    out_rows = []
    for sent_idx, (sent, n_idx) in enumerate(zip(sentences, n_assignments), start=1):
        sent_str = f'S{sent_idx:03d}'  # 한 글에 문장 수가 100+ 가능 → 3자리
        local_id = f'{c_str}-{s_str}-{i_str}-{p_str}-{sent_str}'
        n_chunk_id = f'{c_str}-{s_str}-{i_str}-N{n_idx:02d}' if n_idx else ''
        out_rows.append({
            'db_id': DB_ID,
            'local_id': local_id,
            'local_id_unified': local_id,
            'n_chunk_id': n_chunk_id,
            'line_class': 'TEXT',
            'raw_text': sent,
            'page_info': '',
            'src_metadata': json.dumps({
                'folder': folder.name,
                'version': version,
                'publish_date': manifest_row.get('publish_date'),
                'tonggwon': manifest_row.get('tonggwon'),
                'title': manifest_row.get('title'),
                'section': manifest_row.get('section', ''),
                'cnts_id': manifest_row.get('cnts_id', ''),
            }, ensure_ascii=False),
        })
    return out_rows


def write_xlsx(out_path: Path, all_rows: list):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Sheet1'
    headers = ['uid', 'db_id', 'local_id', 'local_id_unified', 'n_chunk_id',
               'line_class', 'raw_text', 'page_info', 'src_metadata']
    ws.append(headers)
    for i, r in enumerate(all_rows, start=1):
        uid = f'{r["db_id"]}_{i:05d}'
        ws.append([
            uid, r['db_id'], r['local_id'], r['local_id_unified'], r['n_chunk_id'],
            r['line_class'], r['raw_text'], r['page_info'], r['src_metadata'],
        ])
    wb.save(out_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--series', help='특정 series_index 1편만 (예: 49). dry-run용')
    ap.add_argument('--all', action='store_true', help='86편 일괄')
    args = ap.parse_args()

    # series_index 로드
    series_rows = {}
    with SERIES_INDEX.open(encoding='utf-8') as f:
        for row in csv.DictReader(f):
            sn = int(row['series_index'])
            series_rows[sn] = row
    print(f'series_index 행 수: {len(series_rows)}')

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.series:
        sn = int(args.series)
        row = series_rows.get(sn)
        if row is None:
            print(f'! series_index {sn} not in csv')
            return
        if sn in SKIP_SERIES:
            print(f'  skip series #{sn} (in samples/ folder)')
            return
        print(f'\n=== #{sn} {row["title"][:50]} dry-run ===')
        out_rows = process_one_article(sn, row)
        if out_rows is None:
            print(f'  ! no transcript')
            return
        print(f'  본문 문장 row: {len(out_rows)}')
        n_chunks = sorted(set(r['n_chunk_id'] for r in out_rows if r['n_chunk_id']))
        print(f'  N 묶음 수: {len(n_chunks)}')
        from collections import Counter
        n_counts = Counter(r['n_chunk_id'] for r in out_rows if r['n_chunk_id'])
        for nid in n_chunks:
            print(f'    {nid}: {n_counts[nid]} 문장')
        print(f'  샘플 row (앞 3·중간 3·끝 3):')
        for r in out_rows[:3] + out_rows[len(out_rows)//2-1:len(out_rows)//2+2] + out_rows[-3:]:
            text_short = r['raw_text'][:50] + ('...' if len(r['raw_text']) > 50 else '')
            print(f'    {r["local_id"]} | {r["n_chunk_id"]:18} | {text_short}')

    elif args.all:
        all_rows = []
        skip_log = []
        for sn in sorted(series_rows.keys()):
            if sn in SKIP_SERIES:
                skip_log.append(f'  skip #{sn} (sample folder)')
                continue
            row = series_rows[sn]
            article_rows = process_one_article(sn, row)
            if article_rows is None:
                skip_log.append(f'  ! #{sn} no transcript: {row.get("title", "")[:30]}')
                continue
            all_rows.extend(article_rows)
        if skip_log:
            print('\n'.join(skip_log))
        print(f'\n총 row: {len(all_rows)}')
        out_path = OUT_DIR / 'MA_YD_10-20_WB.xlsx'
        write_xlsx(out_path, all_rows)
        print(f'Saved: {out_path}')


if __name__ == '__main__':
    main()
