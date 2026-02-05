# -*- coding: utf-8 -*-
"""
人乃天主義 전체 분포 및 용례 보고서
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

# 장 추출
matches['chapter'] = matches['local_id'].str.extract(r'^(C\d+)')

print('=' * 80)
print('【표 1】 『인내천요의』 전체 장별 人乃天主義 분포')
print('=' * 80)
print()
print('| 장 | 제목 | 빈도 | 용례 (일부) |')
print('|:---|:-----|:----:|:------------|')

chapter_titles = {
    'C01': '緖言',
    'C02': '人乃天과 天道',
    'C03': '人乃天과 眞理',
    'C04': '人乃天의 目的',
    'C05': '人乃天의 修煉',
    'C06': '인내천의 雜感',
}

for ch in ['C01', 'C02', 'C03', 'C04', 'C05', 'C06']:
    ch_matches = matches[matches['chapter'] == ch]
    cnt = len(ch_matches)
    title = chapter_titles.get(ch, '')

    if cnt > 0:
        # 첫 번째 용례
        first_text = ch_matches.iloc[0]['kr_text']
        # 人乃天主義 앞뒤 문맥 추출
        match = re.search(r'.{0,15}人乃天主義.{0,15}', str(first_text))
        if match:
            example = '...' + match.group() + '...'
        else:
            example = first_text[:40] + '...'
        print(f'| {ch} | {title} | {cnt}회 | {example} |')
    else:
        print(f'| {ch} | {title} | 0회 | - |')

print(f'| **합계** | | **{len(matches)}회** | |')

print()
print()
print('=' * 80)
print('【표 2】 제3장 절별 분포')
print('=' * 80)
print()
print('| 절 | 제목 | 빈도 | 용례 (일부) |')
print('|:---|:-----|:----:|:------------|')

c03_matches = matches[matches['chapter'] == 'C03'].copy()
c03_matches['section'] = c03_matches['local_id'].str.extract(r'^(C03-S\d+)')

section_titles = {
    'C03-S01': '天道敎의 宗旨',
    'C03-S02': '人乃天의 發源',
    'C03-S03': '人乃天의 信仰',
    'C03-S04': '人乃天의 哲理',
}

for sec in ['C03-S01', 'C03-S02', 'C03-S03', 'C03-S04']:
    sec_matches = c03_matches[c03_matches['section'] == sec]
    cnt = len(sec_matches)
    title = section_titles.get(sec, '')

    if cnt > 0:
        first_text = sec_matches.iloc[0]['kr_text']
        match = re.search(r'.{0,15}人乃天主義.{0,15}', str(first_text))
        if match:
            example = '...' + match.group() + '...'
        else:
            example = first_text[:40] + '...'
        print(f'| {sec} | {title} | {cnt}회 | {example} |')
    else:
        print(f'| {sec} | {title} | 0회 | - |')

print(f'| **합계** | | **{len(c03_matches)}회** | |')

print()
print()
print('=' * 80)
print('【표 3】 제3장 4절 항별 분포')
print('=' * 80)
print()
print('| 위치 | 제목 | 빈도 | 용례 (일부) |')
print('|:---|:-----|:----:|:------------|')

c03s04_matches = c03_matches[c03_matches['section'] == 'C03-S04'].copy()

# 서두 (I가 없는 것)
c03s04_matches['is_intro'] = ~c03s04_matches['local_id'].str.contains('-I\d+', regex=True)
c03s04_matches['item'] = c03s04_matches['local_id'].str.extract(r'(C03-S04-I\d+)')

item_titles = {
    'intro': '(서두)',
    'C03-S04-I01': '實現思想과 人乃天',
    'C03-S04-I02': '實在와 人乃天',
    'C03-S04-I03': '汎神觀과 人乃天',
    'C03-S04-I04': '生命과 人乃天',
    'C03-S04-I05': '意識과 人乃天',
    'C03-S04-I06': '靈魂과 人乃天',
    'C03-S04-I07': '進化와 人乃天',
}

# 서두
intro_matches = c03s04_matches[c03s04_matches['is_intro']]
if len(intro_matches) > 0:
    first_text = intro_matches.iloc[0]['kr_text']
    match = re.search(r'.{0,15}人乃天主義.{0,15}', str(first_text))
    if match:
        example = '...' + match.group() + '...'
    else:
        example = first_text[:40] + '...'
    print(f'| 서두 | (원리상/응용상 구분) | {len(intro_matches)}회 | {example} |')
else:
    print(f'| 서두 | (원리상/응용상 구분) | 0회 | - |')

# 각 항
for item in ['C03-S04-I01', 'C03-S04-I02', 'C03-S04-I03', 'C03-S04-I04',
             'C03-S04-I05', 'C03-S04-I06', 'C03-S04-I07']:
    item_matches = c03s04_matches[c03s04_matches['item'] == item]
    cnt = len(item_matches)
    title = item_titles.get(item, '')
    item_short = item.replace('C03-S04-', '')

    if cnt > 0:
        first_text = item_matches.iloc[0]['kr_text']
        match = re.search(r'.{0,15}人乃天主義.{0,15}', str(first_text))
        if match:
            example = '...' + match.group() + '...'
        else:
            example = first_text[:40] + '...'
        print(f'| {item_short} | {title} | {cnt}회 | {example} |')
    else:
        print(f'| {item_short} | {title} | 0회 | - |')

print(f'| **합계** | | **{len(c03s04_matches)}회** | |')
