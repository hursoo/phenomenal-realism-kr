# -*- coding: utf-8 -*-
"""
맹장(Mechnikov) 구간 - 기존 crosstab 데이터 확인
"""
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

df_old = pd.read_csv('data/analysis/crosstab_similarity_data.csv')
df_old = df_old.set_index('section_id')

print('【기존 crosstab 데이터: C08 행】')
print('=' * 60)

c08_row = df_old.loc['C08']
# 상위 5개
top5 = c08_row.nlargest(5)
print("C08의 최대 유사도 상위 5개 절:")
for col, val in top5.items():
    print(f"  C08 × {col}: {val:.4f}")

print()
print('【C08 × C03-S04 유사도】')
print('-' * 40)
if 'C03-S04' in df_old.columns:
    val = df_old.loc['C08', 'C03-S04']
    print(f"  C08 × C03-S04: {val:.4f}")
else:
    print("  C03-S04 열 없음")

# 0.5259가 어디서 나왔는지 찾기
print()
print('【0.52 이상 유사도 구간 검색】')
print('-' * 40)
for idx in df_old.index:
    for col in df_old.columns:
        val = df_old.loc[idx, col]
        if val >= 0.52:
            print(f"  {idx} × {col}: {val:.4f}")
