# -*- coding: utf-8 -*-
"""
人乃天主義 분포 엑셀 저장 (출현 횟수 기준)
"""
import pandas as pd
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_excel('app/data/BK_YD_1924_IY_v1.2.xlsx')
df = df[df['line_class'].isin(['TEXT', 'STRUCT'])]

# 출현 횟수 계산
df['count'] = df['kr_text'].apply(lambda x: len(re.findall(r'人乃天主義', str(x))))

def get_example(subset):
    """첫 번째 용례 추출"""
    for _, row in subset.iterrows():
        if row['count'] > 0:
            match = re.search(r'.{0,20}人乃天主義.{0,20}', str(row['kr_text']))
            if match:
                return '...' + match.group() + '...'
    return '-'

# 표 1: 장별 분포
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
    ch_rows = df[df['local_id'].str.startswith(ch, na=False)]
    cnt = ch_rows['count'].sum()
    example = get_example(ch_rows[ch_rows['count'] > 0])
    chapter_data.append({'장': ch, '제목': title, '빈도': int(cnt), '대표 용례': example})

df_chapter = pd.DataFrame(chapter_data)

# 표 2: 제3장 절별 분포
section_data = []
section_info = [
    ('C03-S01', '天道敎의 宗旨'),
    ('C03-S02', '人乃天의 發源'),
    ('C03-S03', '人乃天의 信仰'),
    ('C03-S04', '人乃天의 哲理'),
]

for sec, title in section_info:
    sec_rows = df[df['local_id'].str.startswith(sec, na=False)]
    cnt = sec_rows['count'].sum()
    example = get_example(sec_rows[sec_rows['count'] > 0])
    section_data.append({'절': sec.replace('C03-', ''), '제목': title, '빈도': int(cnt), '대표 용례': example})

df_section = pd.DataFrame(section_data)

# 표 3: 제3장 4절 항별 분포
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

c03s04 = df[df['local_id'].str.startswith('C03-S04', na=False)].copy()

for item, title in item_info:
    if item == '서두':
        item_rows = c03s04[~c03s04['local_id'].str.contains(r'-I\d+', regex=True)]
    else:
        item_rows = c03s04[c03s04['local_id'].str.contains(f'C03-S04-{item}', regex=False)]

    cnt = item_rows['count'].sum()
    example = get_example(item_rows[item_rows['count'] > 0])
    item_data.append({'항': item, '제목': title, '빈도': int(cnt), '대표 용례': example})

df_item = pd.DataFrame(item_data)

# 엑셀 저장
output_path = 'app/data/人乃天主義_분포.xlsx'
with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
    df_chapter.to_excel(writer, sheet_name='장별 분포', index=False)
    df_section.to_excel(writer, sheet_name='제3장 절별 분포', index=False)
    df_item.to_excel(writer, sheet_name='제3장4절 항별 분포', index=False)

print(f'저장 완료: {output_path}')
print()
print('【표 3 확인】')
print(df_item.to_string(index=False))
