# -*- coding: utf-8 -*-
"""
검증된 111개 참조쌍 기준 통계 재산출
"""
import pandas as pd
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 유효 쌍만 로드
df = pd.read_csv('data/analysis/validated_pairs_final.csv')
print(f'【검증된 유효 참조쌍: {len(df)}개】')
print('=' * 80)

# 1915 장 추출
df['ch_1915'] = df['pid_1915'].apply(lambda x: re.match(r'(C\d+)', str(x)).group(1) if re.match(r'(C\d+)', str(x)) else None)

# 1924 장/절 추출
df['ch_1924'] = df['pid_1924'].apply(lambda x: re.match(r'(C\d+)', str(x)).group(1) if re.match(r'(C\d+)', str(x)) else None)
df['sect_1924'] = df['pid_1924'].apply(lambda x: re.match(r'(C\d+-S\d+)', str(x)).group(1) if re.match(r'(C\d+-S\d+)', str(x)) else None)

# 주요 구간별 통계
print('\n【주요 구간별 참조쌍 개수 (발표문 서술 관련)】')
print('-' * 60)

# C06 × C03-S04 (생명의 정의)
c06_c03s04 = df[(df['ch_1915'] == 'C06') & (df['sect_1924'] == 'C03-S04')]
print(f'C06 × C03-S04 (생명의 정의): {len(c06_c03s04)}개')

# C08 × C03-S04 (메치니코프/맹장)
c08_c03s04 = df[(df['ch_1915'] == 'C08') & (df['sect_1924'] == 'C03-S04')]
print(f'C08 × C03-S04 (메치니코프): {len(c08_c03s04)}개')

# C07 × C03-S04 (나가이 비평 - 필터링 구간)
c07_c03s04 = df[(df['ch_1915'] == 'C07') & (df['sect_1924'] == 'C03-S04')]
print(f'C07 × C03-S04 (나가이 비평): {len(c07_c03s04)}개')

# C13 × C06 (기독교와 유교)
c13_c06 = df[(df['ch_1915'] == 'C13') & (df['ch_1924'] == 'C06')]
print(f'C13 × C06 (기독교와 유교): {len(c13_c06)}개')

# C14 × C06 (기독교와 불교)
c14_c06 = df[(df['ch_1915'] == 'C14') & (df['ch_1924'] == 'C06')]
print(f'C14 × C06 (기독교와 불교): {len(c14_c06)}개')

# C02 × C03 (현상즉실재론)
c02_c03 = df[(df['ch_1915'] == 'C02') & (df['ch_1924'] == 'C03')]
print(f'C02 × C03 (현상즉실재론): {len(c02_c03)}개')

# 전체 장-장 매트릭스
print('\n' + '=' * 80)
print('【장-장 매트릭스 (count)】')
print('-' * 60)

ch_ch_matrix = df.groupby(['ch_1915', 'ch_1924']).size().unstack(fill_value=0)
print(ch_ch_matrix.to_string())

# 장-절 매트릭스 (C03 세부)
print('\n' + '=' * 80)
print('【1915장 × C03 절별 분포】')
print('-' * 60)

c03_df = df[df['ch_1924'] == 'C03']
c03_sect_matrix = c03_df.groupby(['ch_1915', 'sect_1924']).size().unstack(fill_value=0)
if len(c03_sect_matrix) > 0:
    print(c03_sect_matrix.to_string())

# C06 세부
print('\n【1915장 × C06 절별 분포】')
print('-' * 60)

c06_df = df[df['ch_1924'] == 'C06']
c06_sect_matrix = c06_df.groupby(['ch_1915', 'sect_1924']).size().unstack(fill_value=0)
if len(c06_sect_matrix) > 0:
    print(c06_sect_matrix.to_string())

# 저장
ch_ch_matrix.to_csv('data/analysis/validated_chapter_chapter_matrix.csv')
print(f'\n저장: data/analysis/validated_chapter_chapter_matrix.csv')
