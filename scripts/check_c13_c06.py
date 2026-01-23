# -*- coding: utf-8 -*-
"""
C13 × C06 문단 쌍 상세 분석 (33개)
"""
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_csv('data/analysis/paragraph_similarity_top500.csv')

# C13 × C06 필터링
pairs = df[(df['chapter_1915'] == 'C13') & (df['section_1924'].str.startswith('C06'))]

print('【C13 × C06 문단 쌍 분석】')
print('=' * 80)
print(f'상위 500개 중 C13 × C06: {len(pairs)}개')
print()

# 1915 C13 장 제목 확인
df_1915 = pd.read_excel('app/data/BK_IT_1915_PR_v1.3.xlsx')
c13_title = df_1915[df_1915['local_id'] == 'C13']['kr_text'].values
if len(c13_title) > 0:
    print(f"【1915 C13 제목】: {c13_title[0]}")

# 1924 C06 장 제목 확인
df_1924 = pd.read_excel('app/data/BK_YD_1924_IY_v1.2.xlsx')
c06_title = df_1924[df_1924['local_id'] == 'C06']['kr_text'].values
if len(c06_title) > 0:
    print(f"【1924 C06 제목】: {c06_title[0]}")

print()
print('=' * 80)

# 유사도 ≥ 0.1 쌍만 출력
pairs_above = pairs[pairs['similarity'] >= 0.1]
print(f"\n유사도 ≥ 0.1인 쌍: {len(pairs_above)}개\n")

for i, (_, row) in enumerate(pairs_above.iterrows(), 1):
    print(f"【{i}/{len(pairs_above)}】 순위 {row['rank']:3d}위 | 유사도: {row['similarity']:.4f}")
    print(f"  문단: {row['pid_1915']} × {row['pid_1924']}")
    print(f"  [1915] {row['text_1915'][:200]}...")
    print(f"  [1924] {row['text_1924'][:200]}...")
    print()
