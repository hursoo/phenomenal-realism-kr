# -*- coding: utf-8 -*-
"""
맹장(Mechnikov) 구간 검증
"""
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 1915 텍스트에서 메치니코프/맹장 검색
df_1915 = pd.read_excel('app/data/BK_IT_1915_PR_v1.3.xlsx')
df_1924 = pd.read_excel('app/data/BK_YD_1924_IY_v1.2.xlsx')

print('【1915 텍스트: メチニコフ/盲腸 검색】')
print('=' * 60)
mask = df_1915['kr_text'].str.contains('メチニコフ|盲腸', na=False, regex=True)
results = df_1915[mask][['local_id', 'kr_text']]
for _, row in results.iterrows():
    print(f"{row['local_id']}: {row['kr_text'][:80]}...")
print(f"\n총 {len(results)}개 문장")

print()
print('【1924 텍스트: 盲腸/맹장 검색】')
print('=' * 60)
mask = df_1924['kr_text'].str.contains('盲腸|맹장', na=False, regex=True)
results = df_1924[mask][['local_id', 'kr_text']]
for _, row in results.iterrows():
    print(f"{row['local_id']}: {row['kr_text'][:80]}...")
print(f"\n총 {len(results)}개 문장")
