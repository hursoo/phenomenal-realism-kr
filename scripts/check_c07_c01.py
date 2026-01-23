# -*- coding: utf-8 -*-
"""
C07 × C01 문단 쌍 확인
"""
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_csv('data/analysis/paragraph_similarity_top500.csv')

# C07 × C01 필터링
pairs = df[(df['chapter_1915'] == 'C07') & (df['section_1924'].str.startswith('C01'))]

print('【C07 × C01 문단 쌍】')
print('=' * 70)
print(f'상위 500개 중 C07 × C01: {len(pairs)}개')
print()

for _, row in pairs.iterrows():
    print(f"【{row['rank']:3d}위】 유사도: {row['similarity']:.4f}")
    print(f"  문단 ID: {row['pid_1915']} × {row['pid_1924']}")
    print(f"  ─" * 35)
    print(f"  【1915 C07】")
    print(f"  {row['text_1915']}")
    print()
    print(f"  【1924 C01】")
    print(f"  {row['text_1924']}")
    print()
    print("=" * 70)
    print()
