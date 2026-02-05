# -*- coding: utf-8 -*-
"""
한 문장에 人乃天主義가 여러 번 나오는 경우 확인
"""
import pandas as pd
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_excel('app/data/BK_YD_1924_IY_v1.2.xlsx')
df = df[df['line_class'].isin(['TEXT', 'STRUCT'])]

# C03-S04
c03s04 = df[df['local_id'].str.startswith('C03-S04', na=False)].copy()
c03s04['count'] = c03s04['kr_text'].apply(lambda x: len(re.findall(r'人乃天主義', str(x))))

# 1회 이상 나오는 행
matches = c03s04[c03s04['count'] > 0]

print('【C03-S04 내 人乃天主義 출현 횟수】')
print('=' * 80)

total = 0
for _, row in matches.iterrows():
    cnt = row['count']
    total += cnt
    marker = ' ★' if cnt > 1 else ''
    print(f"[{cnt}회] {row['local_id']}{marker}")
    if cnt > 1:
        print(f"     → {row['kr_text'][:100]}...")

print()
print(f"총 출현 횟수: {total}회 (문장 수: {len(matches)}개)")
