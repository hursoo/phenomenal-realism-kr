# -*- coding: utf-8 -*-
"""
應用上 人乃天主義 관련 언급 검색
"""
import pandas as pd
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_excel('app/data/BK_YD_1924_IY_v1.2.xlsx')
df = df[df['line_class'].isin(['TEXT', 'STRUCT'])]

# 應用 관련 검색
print('【應用上 人乃天主義 관련 언급 검색】')
print('=' * 80)

# 1. 應用上 人乃天主義 직접 언급
print('\n1. "應用上 人乃天主義" 직접 언급:')
print('-' * 80)
matches1 = df[df['kr_text'].str.contains('應用上 人乃天主義', na=False)]
for _, row in matches1.iterrows():
    print(f"[{row['local_id']}]")
    print(f"  {row['kr_text']}")
    print()

# 2. 應用上 + 人乃天 조합
print('\n2. "應用上" 언급 전체:')
print('-' * 80)
matches2 = df[df['kr_text'].str.contains('應用上', na=False)]
for _, row in matches2.iterrows():
    print(f"[{row['local_id']}]")
    print(f"  {row['kr_text']}")
    print()

# 3. 原理上 vs 應用上 구분 언급
print('\n3. "原理" 와 "應用" 동시 언급:')
print('-' * 80)
matches3 = df[df['kr_text'].str.contains('原理', na=False) & df['kr_text'].str.contains('應用', na=False)]
for _, row in matches3.iterrows():
    print(f"[{row['local_id']}]")
    print(f"  {row['kr_text']}")
    print()
