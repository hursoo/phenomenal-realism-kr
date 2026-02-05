# -*- coding: utf-8 -*-
"""
인내천요의 제3장 4절 (C03-S04) 구조 분석
"""
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_excel('app/data/BK_YD_1924_IY_v1.2.xlsx')

# C03-S04 구조 파악
print('【인내천요의 제3장 4절 (C03-S04) 구조】')
print('=' * 70)

c03s04 = df[df['local_id'].str.startswith('C03-S04', na=False)]

# STRUCT만 추출하여 계층 구조 파악
structs = c03s04[c03s04['line_class'] == 'STRUCT'][['local_id', 'kr_text']]
print('\n【절/항 구조】')
for _, row in structs.iterrows():
    depth = row['local_id'].count('-') - 1
    indent = '  ' * depth
    print(f"{indent}{row['local_id']}: {row['kr_text']}")

# 각 항(I)별 문단 수 집계
print('\n【항별 문단 수】')
texts = c03s04[c03s04['line_class'] == 'TEXT']
texts['item'] = texts['local_id'].str.extract(r'(C03-S04-I\d+)')
item_counts = texts.groupby('item').size()
for item, cnt in item_counts.items():
    if pd.notna(item):
        print(f"  {item}: {cnt}개 문장")
