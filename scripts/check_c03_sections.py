# -*- coding: utf-8 -*-
"""
C03 내 유사도 ≥ 0.1 쌍의 섹션별 분포 확인
"""
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 상위 500개 쌍 로드
df = pd.read_csv('data/analysis/paragraph_similarity_top500.csv')

# 유사도 0.1 이상만
df = df[df['similarity'] >= 0.1]

# C03 관련만 필터
c03 = df[df['pid_1924'].str.startswith('C03')]

print('【C03 내 유사도 ≥ 0.1 쌍 분포】')
print('=' * 60)

# 섹션별 분류
for sec in ['C03-S01', 'C03-S02', 'C03-S03', 'C03-S04']:
    sec_df = c03[c03['pid_1924'].str.startswith(sec)]
    print(f'{sec}: {len(sec_df)}개')

print()
print(f'C03 전체: {len(c03)}개')
print()

# S04 이외 쌍 상세
non_s04 = c03[~c03['pid_1924'].str.startswith('C03-S04')]
if len(non_s04) > 0:
    print('【S04 이외의 쌍 상세】')
    print('-' * 60)
    for _, row in non_s04.iterrows():
        print(f"Rank {row['rank']}: {row['pid_1915']} × {row['pid_1924']}")
        print(f"  유사도: {row['similarity']:.4f}")
        print(f"  1915 텍스트: {row['text_1915'][:80]}...")
        print(f"  1924 텍스트: {row['text_1924'][:80]}...")
        print()
        print()
