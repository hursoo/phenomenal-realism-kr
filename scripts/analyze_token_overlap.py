# -*- coding: utf-8 -*-
"""
토큰 오버랩 비교 분석: C01×C03 vs C06×C03-S04
"""
import pandas as pd
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_csv('data/analysis/paragraph_similarity_top500.csv')

def get_hanja_tokens(text):
    return set(re.findall(r'[一-龥]{2,}', str(text)))

# === C01 × C03 ===
print('【C01 × C03 - 토큰 분석】')
print('=' * 80)
pairs1 = df[(df['chapter_1915'] == 'C01') & (df['section_1924'].str.startswith('C03'))]
pairs1 = pairs1[pairs1['similarity'] >= 0.1]

for i, (_, row) in enumerate(pairs1.iterrows(), 1):
    common = get_hanja_tokens(row['text_1915']) & get_hanja_tokens(row['text_1924'])
    print(f"  {i}. 순위 {row['rank']:3d}위 | 공통 {len(common)}개: {sorted(common)}")

# === C06 × C03-S04 (비교용) ===
print('\n【C06 × C03-S04 - 토큰 분석 (상위 5개)】')
print('=' * 80)
pairs2 = df[(df['chapter_1915'] == 'C06') & (df['section_1924'].str.startswith('C03-S04'))]
pairs2 = pairs2[pairs2['similarity'] >= 0.1].head(5)

for i, (_, row) in enumerate(pairs2.iterrows(), 1):
    common = get_hanja_tokens(row['text_1915']) & get_hanja_tokens(row['text_1924'])
    print(f"  {i}. 순위 {row['rank']:3d}위 | 공통 {len(common)}개: {sorted(common)}")
