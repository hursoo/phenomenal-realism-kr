# -*- coding: utf-8 -*-
"""
문단 단위 자카드 유사도 산출 스크립트
=====================================
산출일: 2026-01-23
목적: 1915 『철학과 종교』와 1924 『인내천요의』 간 문단 단위 유사도 분석

필터링 조건:
- 포함: line_class = 'TEXT'
- 제외: structure_id = 'TOC', 'ROOT'

산출물:
1. paragraph_similarity_top500.csv - 상위 500개 문단 쌍
2. chapter_section_matrix.csv - 장-절 단위 집계 (29×25), mean
3. chapter_chapter_matrix.csv - 장-장 단위 집계 (29×6), mean
4. similarity_stats.json - 통계 요약
"""

import pandas as pd
import numpy as np
import re
import json
from collections import defaultdict
from itertools import product
import sys
import os

# 출력 인코딩 설정
sys.stdout.reconfigure(encoding='utf-8')

# 경로 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'app', 'data')
OUTPUT_DIR = os.path.join(BASE_DIR, 'data', 'analysis')

# 출력 디렉토리 생성
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 70)
print("【문단 단위 자카드 유사도 산출】")
print("=" * 70)

# =============================================================================
# 1. 데이터 로드 및 전처리
# =============================================================================
print("\n[1/5] 데이터 로드 및 전처리...")

df_1915 = pd.read_excel(os.path.join(DATA_DIR, 'BK_IT_1915_PR_v1.3.xlsx'))
df_1924 = pd.read_excel(os.path.join(DATA_DIR, 'BK_YD_1924_IY_v1.2.xlsx'))

# 필터링: TEXT만, TOC/ROOT 제외
df_1915_text = df_1915[df_1915['line_class'] == 'TEXT']
df_1915_text = df_1915_text[~df_1915_text['structure_id'].isin(['TOC', 'ROOT'])]

df_1924_text = df_1924[df_1924['line_class'] == 'TEXT']
df_1924_text = df_1924_text[~df_1924_text['structure_id'].isin(['TOC', 'ROOT'])]

print(f"  - 1915 TEXT 행: {len(df_1915_text)}")
print(f"  - 1924 TEXT 행: {len(df_1924_text)}")

# =============================================================================
# 2. 문단 ID 추출 및 텍스트 결합
# =============================================================================
print("\n[2/5] 문단 단위 텍스트 결합...")

def extract_paragraph_id_1915(local_id):
    """1915 텍스트 문단 ID 추출 (C##-P## 또는 C##-S##-P##)"""
    if pd.isna(local_id):
        return None
    local_id = str(local_id)
    match1 = re.match(r'(C\d+-P\d+)', local_id)
    if match1:
        return match1.group(1)
    match2 = re.match(r'(C\d+-S\d+-P\d+)', local_id)
    if match2:
        return match2.group(1)
    return None

def extract_paragraph_id_1924(local_id):
    """1924 텍스트 문단 ID 추출 (C##-S##-P## 또는 C##-S##-I##-P##)"""
    if pd.isna(local_id):
        return None
    local_id = str(local_id)
    match = re.match(r'(C\d+-S\d+(?:-I\d+)?-P\d+)', local_id)
    return match.group(1) if match else None

def extract_chapter(para_id):
    """문단 ID에서 장(Chapter) 추출"""
    if para_id is None:
        return None
    match = re.match(r'(C\d+)', para_id)
    return match.group(1) if match else None

def extract_section_1924(para_id):
    """1924 문단 ID에서 절(Section) 추출 (C##-S##)"""
    if para_id is None:
        return None
    match = re.match(r'(C\d+-S\d+)', para_id)
    return match.group(1) if match else None

# 문단 ID 추출
df_1915_text = df_1915_text.copy()
df_1924_text = df_1924_text.copy()

df_1915_text['paragraph_id'] = df_1915_text['local_id'].apply(extract_paragraph_id_1915)
df_1924_text['paragraph_id'] = df_1924_text['local_id'].apply(extract_paragraph_id_1924)

# 문단별 텍스트 결합
paragraphs_1915 = df_1915_text.groupby('paragraph_id')['kr_text'].apply(
    lambda x: ' '.join(x.dropna().astype(str))
).to_dict()

paragraphs_1924 = df_1924_text.groupby('paragraph_id')['kr_text'].apply(
    lambda x: ' '.join(x.dropna().astype(str))
).to_dict()

# None 키 제거
paragraphs_1915 = {k: v for k, v in paragraphs_1915.items() if k is not None}
paragraphs_1924 = {k: v for k, v in paragraphs_1924.items() if k is not None}

print(f"  - 1915 문단 수: {len(paragraphs_1915)}")
print(f"  - 1924 문단 수: {len(paragraphs_1924)}")
print(f"  - 총 비교 쌍: {len(paragraphs_1915) * len(paragraphs_1924):,}")

# =============================================================================
# 3. 한자어 토큰화 및 자카드 유사도 계산
# =============================================================================
print("\n[3/5] 한자어 토큰화 및 유사도 계산...")

def extract_hanja_tokens(text):
    """텍스트에서 2자 이상 한자어 추출"""
    if not text or pd.isna(text):
        return set()
    # 한자 범위: CJK Unified Ideographs
    pattern = r'[一-龥]{2,}'
    tokens = re.findall(pattern, str(text))
    return set(tokens)

def jaccard_similarity(set1, set2):
    """자카드 유사도 계산"""
    if not set1 or not set2:
        return 0.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0

# 각 문단의 한자어 토큰 추출 (캐싱)
tokens_1915 = {pid: extract_hanja_tokens(text) for pid, text in paragraphs_1915.items()}
tokens_1924 = {pid: extract_hanja_tokens(text) for pid, text in paragraphs_1924.items()}

# 모든 문단 쌍의 유사도 계산
print("  - 유사도 계산 중... (약간의 시간이 소요됩니다)")

similarities = []
total_pairs = len(paragraphs_1915) * len(paragraphs_1924)
processed = 0

for pid_1915, tokens_1 in tokens_1915.items():
    chapter_1915 = extract_chapter(pid_1915)

    for pid_1924, tokens_2 in tokens_1924.items():
        sim = jaccard_similarity(tokens_1, tokens_2)
        chapter_1924 = extract_chapter(pid_1924)
        section_1924 = extract_section_1924(pid_1924)

        similarities.append({
            'pid_1915': pid_1915,
            'pid_1924': pid_1924,
            'similarity': sim,
            'chapter_1915': chapter_1915,
            'chapter_1924': chapter_1924,
            'section_1924': section_1924
        })

    processed += len(tokens_1924)
    if processed % 50000 == 0:
        print(f"    진행: {processed:,} / {total_pairs:,} ({processed/total_pairs*100:.1f}%)")

print(f"  - 완료: {len(similarities):,}개 쌍")

# DataFrame 변환
df_sim = pd.DataFrame(similarities)

# =============================================================================
# 4. 산출물 생성
# =============================================================================
print("\n[4/5] 산출물 생성...")

# --- 4.1 상위 500개 문단 쌍 ---
print("  - paragraph_similarity_top500.csv 생성 중...")

df_top500 = df_sim.nlargest(500, 'similarity').copy()

# 텍스트 미리보기 추가 (앞 50자)
df_top500['text_1915'] = df_top500['pid_1915'].apply(
    lambda x: paragraphs_1915.get(x, '')[:80] + '...' if len(paragraphs_1915.get(x, '')) > 80 else paragraphs_1915.get(x, '')
)
df_top500['text_1924'] = df_top500['pid_1924'].apply(
    lambda x: paragraphs_1924.get(x, '')[:80] + '...' if len(paragraphs_1924.get(x, '')) > 80 else paragraphs_1924.get(x, '')
)

# 순위 추가
df_top500.insert(0, 'rank', range(1, 501))

df_top500.to_csv(
    os.path.join(OUTPUT_DIR, 'paragraph_similarity_top500.csv'),
    index=False,
    encoding='utf-8-sig'
)

# --- 4.2 장-절 단위 집계 (29×25) ---
print("  - chapter_section_matrix.csv 생성 중...")

# 장-절 조합별 평균 유사도
chapter_section_agg = df_sim.groupby(['chapter_1915', 'section_1924']).agg(
    mean_sim=('similarity', 'mean'),
    max_sim=('similarity', 'max'),
    pair_count=('similarity', 'count')
).reset_index()

# 피벗 테이블 (mean)
pivot_chapter_section = chapter_section_agg.pivot(
    index='chapter_1915',
    columns='section_1924',
    values='mean_sim'
).fillna(0)

pivot_chapter_section.to_csv(
    os.path.join(OUTPUT_DIR, 'chapter_section_matrix.csv'),
    encoding='utf-8-sig'
)

# --- 4.3 장-장 단위 집계 (29×6) ---
print("  - chapter_chapter_matrix.csv 생성 중...")

# 장-장 조합별 평균 유사도
chapter_chapter_agg = df_sim.groupby(['chapter_1915', 'chapter_1924']).agg(
    mean_sim=('similarity', 'mean'),
    max_sim=('similarity', 'max'),
    pair_count=('similarity', 'count')
).reset_index()

# 피벗 테이블 (mean)
pivot_chapter_chapter = chapter_chapter_agg.pivot(
    index='chapter_1915',
    columns='chapter_1924',
    values='mean_sim'
).fillna(0)

pivot_chapter_chapter.to_csv(
    os.path.join(OUTPUT_DIR, 'chapter_chapter_matrix.csv'),
    encoding='utf-8-sig'
)

# --- 4.4 통계 요약 ---
print("  - similarity_stats.json 생성 중...")

stats = {
    'calculation_date': '2026-01-23',
    'filter_conditions': {
        'include': "line_class = 'TEXT'",
        'exclude': "structure_id in ['TOC', 'ROOT']"
    },
    'paragraph_counts': {
        '1915': len(paragraphs_1915),
        '1924': len(paragraphs_1924)
    },
    'total_pairs': len(df_sim),
    'statistics': {
        'mean': round(df_sim['similarity'].mean(), 6),
        'std': round(df_sim['similarity'].std(), 6),
        'min': round(df_sim['similarity'].min(), 6),
        'max': round(df_sim['similarity'].max(), 6),
        'median': round(df_sim['similarity'].median(), 6)
    },
    'percentiles': {
        'P90': round(df_sim['similarity'].quantile(0.90), 6),
        'P95': round(df_sim['similarity'].quantile(0.95), 6),
        'P99': round(df_sim['similarity'].quantile(0.99), 6),
        'P99.5': round(df_sim['similarity'].quantile(0.995), 6)
    },
    'top10_pairs': df_top500.head(10)[['rank', 'pid_1915', 'pid_1924', 'similarity']].to_dict('records')
}

with open(os.path.join(OUTPUT_DIR, 'similarity_stats.json'), 'w', encoding='utf-8') as f:
    json.dump(stats, f, ensure_ascii=False, indent=2)

# =============================================================================
# 5. 결과 요약 출력
# =============================================================================
print("\n[5/5] 결과 요약")
print("=" * 70)

print(f"\n■ 분석 대상")
print(f"  - 1915 문단: {len(paragraphs_1915)}개")
print(f"  - 1924 문단: {len(paragraphs_1924)}개")
print(f"  - 총 비교 쌍: {len(df_sim):,}개")

print(f"\n■ 유사도 통계")
print(f"  - 평균 (μ): {stats['statistics']['mean']:.4f}")
print(f"  - 표준편차 (σ): {stats['statistics']['std']:.4f}")
print(f"  - 최소: {stats['statistics']['min']:.4f}")
print(f"  - 최대: {stats['statistics']['max']:.4f}")

print(f"\n■ 백분위수")
print(f"  - P90: {stats['percentiles']['P90']:.4f}")
print(f"  - P95: {stats['percentiles']['P95']:.4f}")
print(f"  - P99: {stats['percentiles']['P99']:.4f}")
print(f"  - P99.5: {stats['percentiles']['P99.5']:.4f}")

print(f"\n■ 상위 10개 문단 쌍")
for item in stats['top10_pairs']:
    print(f"  {item['rank']:2d}. {item['pid_1915']} × {item['pid_1924']}: {item['similarity']:.4f}")

print(f"\n■ 산출 파일")
print(f"  - {os.path.join(OUTPUT_DIR, 'paragraph_similarity_top500.csv')}")
print(f"  - {os.path.join(OUTPUT_DIR, 'chapter_section_matrix.csv')}")
print(f"  - {os.path.join(OUTPUT_DIR, 'chapter_chapter_matrix.csv')}")
print(f"  - {os.path.join(OUTPUT_DIR, 'similarity_stats.json')}")

print("\n" + "=" * 70)
print("완료!")
print("=" * 70)
