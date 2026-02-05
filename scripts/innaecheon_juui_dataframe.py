# -*- coding: utf-8 -*-
"""
人乃天主義 분포 데이터프레임 생성
"""
import pandas as pd
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_excel('app/data/BK_YD_1924_IY_v1.2.xlsx')
df = df[df['line_class'].isin(['TEXT', 'STRUCT'])]

# 人乃天主義 포함 행 찾기
df['has_term'] = df['kr_text'].apply(lambda x: bool(re.search(r'人乃天主義', str(x))))
matches = df[df['has_term']].copy()

def get_example(text):
    """용례 추출"""
    match = re.search(r'.{0,20}人乃天主義.{0,20}', str(text))
    if match:
        return '...' + match.group() + '...'
    return str(text)[:50] + '...'

# ==========================================
# 표 1: 장별 분포
# ==========================================
chapter_data = []
chapter_info = [
    ('C01', '緖言'),
    ('C02', '人乃天과 天道'),
    ('C03', '人乃天과 眞理'),
    ('C04', '人乃天의 目的'),
    ('C05', '人乃天의 修煉'),
    ('C06', '인내천의 雜感'),
]

for ch, title in chapter_info:
    ch_matches = matches[matches['local_id'].str.startswith(ch, na=False)]
    cnt = len(ch_matches)
    example = get_example(ch_matches.iloc[0]['kr_text']) if cnt > 0 else '-'
    chapter_data.append({'장': ch, '제목': title, '빈도': cnt, '대표 용례': example})

df_chapter = pd.DataFrame(chapter_data)

print('【표 1】 『인내천요의』 장별 人乃天主義 분포')
print('=' * 100)
print(df_chapter.to_string(index=False))
print()

# ==========================================
# 표 2: 제3장 절별 분포
# ==========================================
section_data = []
section_info = [
    ('C03-S01', '天道敎의 宗旨'),
    ('C03-S02', '人乃天의 發源'),
    ('C03-S03', '人乃天의 信仰'),
    ('C03-S04', '人乃天의 哲理'),
]

for sec, title in section_info:
    sec_matches = matches[matches['local_id'].str.startswith(sec, na=False)]
    cnt = len(sec_matches)
    example = get_example(sec_matches.iloc[0]['kr_text']) if cnt > 0 else '-'
    section_data.append({'절': sec.replace('C03-', ''), '제목': title, '빈도': cnt, '대표 용례': example})

df_section = pd.DataFrame(section_data)

print('【표 2】 제3장 절별 人乃天主義 분포')
print('=' * 100)
print(df_section.to_string(index=False))
print()

# ==========================================
# 표 3: 제3장 4절 항별 분포
# ==========================================
item_data = []
item_info = [
    ('서두', '(원리상/응용상 구분)'),
    ('I01', '實現思想과 人乃天'),
    ('I02', '實在와 人乃天'),
    ('I03', '汎神觀과 人乃天'),
    ('I04', '生命과 人乃天'),
    ('I05', '意識과 人乃天'),
    ('I06', '靈魂과 人乃天'),
    ('I07', '進化와 人乃天'),
]

c03s04_matches = matches[matches['local_id'].str.startswith('C03-S04', na=False)].copy()

for item, title in item_info:
    if item == '서두':
        item_matches = c03s04_matches[~c03s04_matches['local_id'].str.contains('-I\\d+', regex=True)]
    else:
        item_matches = c03s04_matches[c03s04_matches['local_id'].str.contains(f'C03-S04-{item}', regex=False)]

    cnt = len(item_matches)
    example = get_example(item_matches.iloc[0]['kr_text']) if cnt > 0 else '-'
    item_data.append({'항': item, '제목': title, '빈도': cnt, '대표 용례': example})

df_item = pd.DataFrame(item_data)

print('【표 3】 제3장 4절 항별 人乃天主義 분포')
print('=' * 100)
print(df_item.to_string(index=False))
