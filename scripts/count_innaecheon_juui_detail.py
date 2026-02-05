# -*- coding: utf-8 -*-
"""
인내천주의(人乃天主義) C03 절별 사용 빈도
"""
import pandas as pd
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_excel('app/data/BK_YD_1924_IY_v1.2.xlsx')
df = df[df['line_class'].isin(['TEXT', 'STRUCT'])]

# C03만 필터링
c03 = df[df['local_id'].str.startswith('C03', na=False)].copy()

# 인내천주의 검색
c03['count'] = c03['kr_text'].apply(lambda x: len(re.findall(r'人乃天主義', str(x))))

# 절 추출
c03['section'] = c03['local_id'].str.extract(r'^(C03-S\d+)')

# 절별 카운트
section_counts = c03.groupby('section')['count'].sum()

print('【C03 절별 人乃天主義 사용 빈도】')
print('=' * 50)

# 절 제목 가져오기
section_titles = {
    'C03-S01': '第一節 天道敎의 宗旨',
    'C03-S02': '第二節 人乃天의 發源',
    'C03-S03': '第三節 人乃天의 信仰',
    'C03-S04': '第四節 人乃天의 哲理',
}

for sec, cnt in section_counts.items():
    title = section_titles.get(sec, '')
    print(f'  {sec} ({title}): {int(cnt)}회')

# C03-S04 내 항별 분포
print()
print('【C03-S04 항별 분포】')
print('-' * 50)

c03s04 = c03[c03['local_id'].str.startswith('C03-S04', na=False)].copy()
c03s04['item'] = c03s04['local_id'].str.extract(r'(C03-S04-I\d+)')
item_counts = c03s04.groupby('item')['count'].sum()

item_titles = {
    'C03-S04-I01': '實現思想과 人乃天',
    'C03-S04-I02': '實在와 人乃天',
    'C03-S04-I03': '汎神觀과 人乃天',
    'C03-S04-I04': '生命과 人乃天',
    'C03-S04-I05': '意識과 人乃天',
    'C03-S04-I06': '靈魂과 人乃天',
    'C03-S04-I07': '進化와 人乃天',
}

for item, cnt in item_counts.items():
    if pd.notna(item):
        title = item_titles.get(item, '')
        if cnt > 0:
            print(f'  {item} ({title}): {int(cnt)}회')
