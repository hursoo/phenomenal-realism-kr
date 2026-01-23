# -*- coding: utf-8 -*-
"""
C06 × C03-S04 문단 쌍 상세 확인
"""
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_csv('data/analysis/paragraph_similarity_top500.csv')

# C06 x C03-S04 필터링
pairs = df[(df['chapter_1915'] == 'C06') & (df['section_1924'] == 'C03-S04')]
print(f'【C06 × C03-S04 문단 쌍】 유사도 ≥ 0.1: {len(pairs)}개')
print('=' * 80)

for _, row in pairs.iterrows():
    print(f"\n【{row['rank']:3d}위】 {row['pid_1915']} × {row['pid_1924']}  유사도: {row['similarity']:.4f}")
    print(f"  1915: {row['text_1915'][:100]}...")
    print(f"  1924: {row['text_1924'][:100]}...")
