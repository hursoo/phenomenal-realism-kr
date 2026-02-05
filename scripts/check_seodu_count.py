# -*- coding: utf-8 -*-
"""
C03-S04 서두 人乃天主義 개수 재확인
"""
import pandas as pd
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_excel('app/data/BK_YD_1924_IY_v1.2.xlsx')
df = df[df['line_class'].isin(['TEXT', 'STRUCT'])]

# C03-S04에서 人乃天主義 포함 행
c03s04 = df[df['local_id'].str.startswith('C03-S04', na=False)].copy()
c03s04['has_term'] = c03s04['kr_text'].apply(lambda x: bool(re.search(r'人乃天主義', str(x))))
matches = c03s04[c03s04['has_term']]

print('【C03-S04 내 人乃天主義 전체 목록】')
print('=' * 80)

for _, row in matches.iterrows():
    local_id = row['local_id']
    # I가 있는지 확인
    has_item = bool(re.search(r'-I\d+', local_id))
    location = '본문' if has_item else '서두'
    print(f"[{location}] {local_id}")

print()
print('=' * 80)

# 서두 vs 본문 카운트
seodu = matches[~matches['local_id'].str.contains(r'-I\d+', regex=True)]
bonmun = matches[matches['local_id'].str.contains(r'-I\d+', regex=True)]

print(f"서두 (I 없음): {len(seodu)}개")
print(f"본문 (I 있음): {len(bonmun)}개")
print(f"합계: {len(matches)}개")
