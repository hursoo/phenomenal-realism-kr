"""개벽 .json → 통일 row-level xlsx 변환.

입력: 개벽 manifest + .json (이돈화 글 74편)
출력: MA_YD_10-20_GB.xlsx

처리:
1. paragraphs 단위로 본문 분해
2. 각 paragraph의 text를 *문장* 단위로 추가 분리 (어미 종결 + 구두점)
3. local_id 부여: C##-S00-I00-P##-S## (절 식별은 1차 단순화 — S00 일관)
4. n_chunk_id: 한 글(C) 안 모든 본문 문장을 모아 n=5 비중첩 묶음 (자투리 < 3 → 앞에 통합)
5. 글 번호 C는 발행일 순 (manifest에서 정렬)

옵션:
    --doc-id <id>   특정 글 1편만 변환 (dry-run)
    --all           74편 일괄 변환
    --dry-run       산출만 출력, xlsx 저장 안 함
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

GAEBYEOK_DIR = Path(r'C:\hp_data\0_workspaces\0_srh\magazine\gaebyeok\raw\articles')
MANIFEST = Path(r'C:\hp_data\0_workspaces\0_srh\magazine\gaebyeok\raw\manifest_20260429.tsv')
OUT_DIR = Path(r'C:\hp_data\0_workspaces\0_tnt\hyeonsang\_ocr_experiments\unified_db_2026-05-19\output')

YID_AUTHORS = ('李敦化', '夜雷', '야뢰', '白頭山人', '백두산인', '滄海居士', '창해거사', '猪巖', '저암')
DB_ID = 'MA_YD_10-20_GB'

N = 5
MERGE_THRESHOLD = 3

# 문장 분리 어미 종결 + 구두점
ENDING_PATTERNS = [
    r'ᄒᆞᆯ지어다', r'ᄒᆞ지어다', r'ᄒᆞᆯ진뎌', r'ᄒᆞᆯ지라',
    r'ᄒᆞᄂᆞ니라', r'ᄒᆞ니라', r'ᄒᆞ리오', r'ᄒᆞ리라',
    r'ᄒᆞ도다', r'ᄒᆞ더라',
    r'노라', r'도다', r'더라', r'리오', r'리라', r'지어다', r'진뎌',
    r'\.', r'。', r'!', r'\?',
]
SPLIT_PATTERN = re.compile('(' + '|'.join(ENDING_PATTERNS) + ')')
HANJA = re.compile(r'[一-鿿]')  # 한자 1자 이상 — *실질 문장* 가드용


def split_sentences(text: str) -> list:
    """문장 분리. 입력은 paragraph text. 한자 0개 row(분리자만)는 제외."""
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
            # 가드: 한자 1자 이상 있는 문장만 (분리자만 있는 row, 한자 0개 row 제외)
            if buf.strip() and HANJA.search(buf):
                sentences.append(buf.strip())
            buf = ''
    if buf.strip() and HANJA.search(buf):
        sentences.append(buf.strip())
    return sentences


def load_yid_manifest() -> list:
    """이돈화/필명 글 74편 명단을 발행일 순으로 정렬해 반환."""
    if not MANIFEST.exists():
        raise FileNotFoundError(f'manifest not found: {MANIFEST}')
    rows = []
    with MANIFEST.open(encoding='utf-8') as f:
        rdr = csv.DictReader(f, delimiter='^')
        for r in rdr:
            author = r.get('필자', '') or ''
            if any(a in author for a in YID_AUTHORS):
                rows.append(r)
    # 발행일 순 정렬 (개벽 글의 발행일은 doc_id 또는 별도 필드?)
    # manifest 컬럼은? 일단 doc_id 순으로 우선
    rows.sort(key=lambda r: (r.get('발행일자') or r.get('publish_date') or r.get('자료ID') or ''))
    return rows


def load_article_json(doc_id: str) -> dict:
    p = GAEBYEOK_DIR / (doc_id + '.json')
    if not p.exists():
        return None
    with p.open(encoding='utf-8') as f:
        return json.load(f)


def assign_n_chunks(sentence_count: int) -> list:
    """문장 수 → n_chunk index for each sentence (1-based N number)."""
    chunks = [list(range(i, min(i+N, sentence_count))) for i in range(0, sentence_count, N)]
    if len(chunks) >= 2 and len(chunks[-1]) < MERGE_THRESHOLD:
        chunks[-2].extend(chunks[-1])
        chunks.pop()
    # 각 문장 인덱스에 n_idx (1-based) 부여
    result = [0] * sentence_count
    for n_idx, chunk in enumerate(chunks, start=1):
        for sent_idx in chunk:
            result[sent_idx] = n_idx
    return result


def process_one_article(manifest_row: dict, c_num: int, dry_run: bool = False) -> list:
    """한 글(개벽 .json)을 통일 row 리스트로 변환."""
    doc_id = manifest_row['자료ID']
    art = load_article_json(doc_id)
    if art is None:
        return None
    meta = art.get('meta', {})
    paragraphs = art.get('paragraphs', [])

    # 모든 본문 문장 모으기
    all_sentences = []  # [(p_num, s_num, raw_text, is_heading, page_markers), ...]
    p_num = 0  # P 번호 (1-based)
    for para in paragraphs:
        text = para.get('text', '') or ''
        is_heading = para.get('is_heading', False)
        page_markers = para.get('page_markers', []) or []
        if not text.strip():
            continue
        p_num += 1
        # 제목·저자(is_heading)는 1 단락 = 1 문장으로 처리
        if is_heading:
            all_sentences.append((p_num, 1, text.strip(), True, page_markers))
            continue
        # 본문 paragraph: 문장 분리
        sents = split_sentences(text)
        if not sents:
            # 분리 결과 0이면 통째로 1 문장
            sents = [text.strip()]
        for s_idx, sent in enumerate(sents, start=1):
            all_sentences.append((p_num, s_idx, sent, False, page_markers))

    # 본문(헤딩 아닌) 문장만 N 묶음 부여 대상
    body_indices = [i for i, t in enumerate(all_sentences) if not t[3]]
    n_chunk_map = {}
    if body_indices:
        n_assignments = assign_n_chunks(len(body_indices))
        for local_i, global_i in enumerate(body_indices):
            n_chunk_map[global_i] = n_assignments[local_i]

    # row 생성
    out_rows = []
    for global_i, (p_num, s_num, text, is_heading, page_markers) in enumerate(all_sentences):
        c_str = f'C{c_num:02d}'
        s_str = 'S00'  # 절 무시 — 1차 단순화
        i_str = 'I00'  # 잡지는 I00 강제
        p_str = f'P{p_num:02d}'
        sent_str = f'S{s_num:02d}'
        local_id = f'{c_str}-{s_str}-{i_str}-{p_str}-{sent_str}'
        unified_id = local_id  # 잡지는 통일 형식 그대로
        if is_heading:
            line_class = 'TITLE' if p_num == 1 else 'HEADING'
            n_chunk_id = ''
        else:
            line_class = 'TEXT'
            n_idx = n_chunk_map.get(global_i, 0)
            n_chunk_id = f'{c_str}-{s_str}-{i_str}-N{n_idx:02d}' if n_idx else ''
        out_rows.append({
            'db_id': DB_ID,
            'local_id': local_id,
            'local_id_unified': unified_id,
            'n_chunk_id': n_chunk_id,
            'line_class': line_class,
            'raw_text': unicodedata.normalize('NFC', text),
            'page_info': '|'.join(page_markers) if page_markers else '',
            'src_metadata': json.dumps({
                'doc_id': doc_id,
                'issue_number': meta.get('issue_number'),
                'publish_date': meta.get('publish_date'),
                'title': meta.get('title'),
                'author_raw': manifest_row.get('필자', ''),
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
    g = ap.add_mutually_exclusive_group()
    g.add_argument('--doc-id', help='특정 doc_id 1편만 변환 (dry-run용)')
    g.add_argument('--all', action='store_true', help='74편 일괄 변환')
    ap.add_argument('--dry-run', action='store_true', help='출력만, xlsx 저장 안 함')
    args = ap.parse_args()

    rows = load_yid_manifest()
    print(f'manifest 이돈화/필명 글: {len(rows)}편')

    if args.doc_id:
        # 특정 doc_id 찾기
        target = next((r for r in rows if r.get('자료ID') == args.doc_id), None)
        if target is None:
            print(f'! doc_id {args.doc_id} not in manifest')
            return
        c_num = rows.index(target) + 1
        print(f'\n=== {args.doc_id} (C{c_num:02d}) dry-run ===')
        out_rows = process_one_article(target, c_num)
        if out_rows is None:
            print(f'  ! .json file not found')
            return
        # 통계
        print(f'  총 row: {len(out_rows)}')
        body_rows = [r for r in out_rows if r['line_class'] == 'TEXT']
        heading_rows = [r for r in out_rows if r['line_class'] in ('TITLE', 'HEADING')]
        print(f'  본문 row (TEXT): {len(body_rows)}')
        print(f'  제목·헤딩 row: {len(heading_rows)}')
        # N 묶음 통계
        from collections import Counter
        n_chunks = Counter(r['n_chunk_id'] for r in body_rows if r['n_chunk_id'])
        print(f'  N 묶음 수: {len(n_chunks)}')
        print(f'  N 묶음별 문장 수 분포:')
        for nid, cnt in sorted(n_chunks.items()):
            print(f'    {nid}: {cnt} 문장')
        # 샘플 row
        print(f'\n  샘플 row (앞 5개):')
        for r in out_rows[:5]:
            text_short = r['raw_text'][:40] + ('...' if len(r['raw_text']) > 40 else '')
            print(f'    {r["local_id"]} | {r["n_chunk_id"]:15} | [{r["line_class"]:7}] {text_short}')
        print(f'\n  중간 샘플 (10~15번째 row):')
        for r in out_rows[10:16]:
            text_short = r['raw_text'][:40] + ('...' if len(r['raw_text']) > 40 else '')
            print(f'    {r["local_id"]} | {r["n_chunk_id"]:15} | [{r["line_class"]:7}] {text_short}')

    elif args.all:
        all_rows = []
        for c_num, r in enumerate(rows, start=1):
            doc_id = r['자료ID']
            article_rows = process_one_article(r, c_num)
            if article_rows is None:
                print(f'  ! C{c_num:02d} {doc_id}: json missing, skip')
                continue
            all_rows.extend(article_rows)
        print(f'\n총 row: {len(all_rows)}')
        if not args.dry_run:
            out_path = OUT_DIR / 'MA_YD_10-20_GB.xlsx'
            write_xlsx(out_path, all_rows)
            print(f'Saved: {out_path}')


if __name__ == '__main__':
    main()
