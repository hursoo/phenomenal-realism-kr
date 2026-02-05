# -*- coding: utf-8 -*-
"""
인내천주의(人乃天主義) 장별 사용 빈도
"""
import pandas as pd
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_excel('app/data/BK_YD_1924_IY_v1.2.xlsx')
df = df[df['line_class'].isin(['TEXT', 'STRUCT'])]

# 인내천주의 검색
df['count'] = df['kr_text'].apply(lambda x: len(re.findall(r'人乃天主義', str(x))))

# 장 추출
df['chapter'] = df['local_id'].str.extract(r'^(C\d+)')

# 장별 카운트
chapter_counts = df.groupby('chapter')['count'].sum()
total = chapter_counts.sum()

print('【人乃天主義 장별 사용 빈도】')
print('=' * 40)
for ch, cnt in chapter_counts.items():
    if cnt > 0:
        print(f'  {ch}: {int(cnt)}회')
print('-' * 40)
print(f'  총계: {int(total)}회')
