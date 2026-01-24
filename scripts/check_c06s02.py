# -*- coding: utf-8 -*-
"""
C06-S02 참조쌍 확인
"""
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_excel('app/data/C06_참조분석.xlsx', sheet_name='상세 쌍 목록')
s02 = df[df['섹션'] == 'C06-S02']

print('【C06-S02 참조쌍 상세】')
print('=' * 70)
for _, row in s02.iterrows():
    print(f"1924: {row['1924 문단ID']}")
    print(f"1915: {row['1915 문단ID']} ({row['1915 장']})")
    print(f"유사도: {row['유사도']:.4f}")
    print(f"공통 토큰: {row['공통 토큰']}")

# 해당 문단 내용 확인
df_1924 = pd.read_excel('app/data/BK_YD_1924_IY_v1.2.xlsx')
df_1915 = pd.read_excel('app/data/BK_IT_1915_PR_v1.3.xlsx')

print('\n' + '=' * 70)
print('【1924 텍스트】')
pid_1924 = s02.iloc[0]['1924 문단ID']
rows_1924 = df_1924[df_1924['local_id'].str.startswith(pid_1924, na=False)]
for _, row in rows_1924.iterrows():
    print(row['kr_text'])

print('\n' + '=' * 70)
print('【1915 텍스트】')
pid_1915 = s02.iloc[0]['1915 문단ID']
rows_1915 = df_1915[df_1915['local_id'].str.startswith(pid_1915, na=False)]
for _, row in rows_1915.iterrows():
    print(row['kr_text'])
