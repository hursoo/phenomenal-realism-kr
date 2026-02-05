# -*- coding: utf-8 -*-
"""
0.5259 근처 값 검색
"""
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

df_old = pd.read_csv('data/analysis/crosstab_similarity_data.csv')
df_old = df_old.set_index('section_id')

print('【0.52~0.54 범위 유사도 검색】')
print('=' * 60)
found = []
for idx in df_old.index:
    for col in df_old.columns:
        val = df_old.loc[idx, col]
        if 0.52 <= val <= 0.54:
            found.append((idx, col, val))

found.sort(key=lambda x: x[2], reverse=True)
for idx, col, val in found:
    print(f"  {idx} × {col}: {val:.4f}")

print()
print('【전체 상위 10개 유사도】')
print('-' * 50)
all_values = []
for idx in df_old.index:
    for col in df_old.columns:
        val = df_old.loc[idx, col]
        if pd.notna(val):
            all_values.append((idx, col, val))

all_values.sort(key=lambda x: x[2], reverse=True)
for idx, col, val in all_values[:10]:
    print(f"  {idx} × {col}: {val:.4f}")
