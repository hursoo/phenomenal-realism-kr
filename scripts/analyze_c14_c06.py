# -*- coding: utf-8 -*-
"""
C14 × C06 참조쌍 상세 분석
- 1915 C14: 基督敎と佛敎 (기독교와 불교)
- 1924 C06-S06: 世界三大宗教의 差異点과 人乃天
"""
import pandas as pd
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 데이터 로드
df_valid = pd.read_csv('data/analysis/validated_pairs_final.csv')
df_1915 = pd.read_excel('app/data/BK_IT_1915_PR_v1.3.xlsx')
df_1924 = pd.read_excel('app/data/BK_YD_1924_IY_v1.2.xlsx')

# C14 × C06 필터링
df_valid['ch_1915'] = df_valid['pid_1915'].apply(lambda x: re.match(r'(C\d+)', str(x)).group(1) if re.match(r'(C\d+)', str(x)) else None)
df_valid['ch_1924'] = df_valid['pid_1924'].apply(lambda x: re.match(r'(C\d+)', str(x)).group(1) if re.match(r'(C\d+)', str(x)) else None)

c14_c06 = df_valid[(df_valid['ch_1915'] == 'C14') & (df_valid['ch_1924'] == 'C06')].copy()
print(f'【C14 × C06 유효 참조쌍: {len(c14_c06)}개】')
print('=' * 80)

# 1915 C14 장 정보
print('\n【1915 C14 구조】')
print('-' * 60)
c14_1915 = df_1915[df_1915['local_id'].str.startswith('C14', na=False)]
c14_struct = c14_1915[c14_1915['line_class'] == 'STRUCT']
for _, row in c14_struct.iterrows():
    print(f"{row['local_id']}: {row['kr_text']}")

# 1924 C06-S06 구조
print('\n【1924 C06-S06 구조】')
print('-' * 60)
c06s06_1924 = df_1924[df_1924['local_id'].str.startswith('C06-S06', na=False)]
c06s06_struct = c06s06_1924[c06s06_1924['line_class'] == 'STRUCT']
for _, row in c06s06_struct.iterrows():
    print(f"{row['local_id']}: {row['kr_text']}")

# 1915 문단별 텍스트 가져오기
def get_text_1915(pid):
    rows = df_1915[df_1915['local_id'].str.startswith(pid, na=False)]
    rows = rows[rows['line_class'] == 'TEXT']
    if len(rows) > 0:
        return ' '.join(rows['kr_text'].dropna().astype(str))
    return ''

def get_text_1924(pid):
    rows = df_1924[df_1924['local_id'].str.startswith(pid, na=False)]
    rows = rows[rows['line_class'] == 'TEXT']
    if len(rows) > 0:
        return ' '.join(rows['kr_text'].dropna().astype(str))
    return ''

# 공통 토큰 추출
def extract_common_tokens(text1, text2):
    t1 = set(re.findall(r'[一-龥]{2,}', str(text1)))
    t2 = set(re.findall(r'[一-龥]{2,}', str(text2)))
    return t1 & t2

# 상세 분석
print('\n' + '=' * 80)
print('【C14 × C06 상세 참조쌍 (유사도 순)】')
print('=' * 80)

c14_c06_sorted = c14_c06.sort_values('similarity', ascending=False)

for _, row in c14_c06_sorted.iterrows():
    pid_1915 = row['pid_1915']
    pid_1924 = row['pid_1924']
    sim = row['similarity']

    text_1915 = get_text_1915(pid_1915)
    text_1924 = get_text_1924(pid_1924)
    common = extract_common_tokens(text_1915, text_1924)

    print(f'\n【Rank {row["rank"]}】 유사도: {sim:.4f}')
    print(f'  {pid_1915} × {pid_1924}')
    print(f'  공통 토큰: {common}')
    print(f'  [1915] {text_1915[:150]}...' if len(text_1915) > 150 else f'  [1915] {text_1915}')
    print(f'  [1924] {text_1924[:150]}...' if len(text_1924) > 150 else f'  [1924] {text_1924}')

# 1915 문단별 참조 분포
print('\n' + '=' * 80)
print('【1915 C14 문단별 참조 분포】')
print('-' * 60)

c14_c06['para_1915'] = c14_c06['pid_1915'].apply(lambda x: re.match(r'(C14-S\d+-P\d+|C14-P\d+)', str(x)).group(1) if re.match(r'(C14-S\d+-P\d+|C14-P\d+)', str(x)) else x)
para_1915_counts = c14_c06['para_1915'].value_counts().sort_index()
for para, cnt in para_1915_counts.items():
    text = get_text_1915(para)[:80]
    print(f'{para}: {cnt}개 → {text}...')

# 1924 문단별 참조 분포
print('\n【1924 C06 문단별 참조 분포】')
print('-' * 60)

c14_c06['para_1924'] = c14_c06['pid_1924'].apply(lambda x: re.match(r'(C06-S06-I\d+-P\d+|C06-S06-P\d+)', str(x)).group(1) if re.match(r'(C06-S06-I\d+-P\d+|C06-S06-P\d+)', str(x)) else x)
para_1924_counts = c14_c06['para_1924'].value_counts().sort_index()
for para, cnt in para_1924_counts.items():
    text = get_text_1924(para)[:80]
    print(f'{para}: {cnt}개 → {text}...')

# 비교 항목별 대응 분석
print('\n' + '=' * 80)
print('【佛基 비교 항목별 대응 분석】')
print('=' * 80)

# C14 섹션별 분류
c14_c06['sect_1915'] = c14_c06['pid_1915'].apply(lambda x: re.match(r'(C14-S\d+)', str(x)).group(1) if re.match(r'(C14-S\d+)', str(x)) else 'C14')
sect_counts = c14_c06.groupby('sect_1915').size().sort_index()
print('\n1915 C14 섹션별 참조쌍:')
for sect, cnt in sect_counts.items():
    print(f'  {sect}: {cnt}개')

# 요약
print('\n' + '=' * 80)
print('【요약】')
print('-' * 60)
print(f'총 유효 참조쌍: {len(c14_c06)}개')
print(f'1915 참조 문단: {len(para_1915_counts)}개')
print(f'1924 참조 문단: {len(para_1924_counts)}개')
print(f'평균 유사도: {c14_c06["similarity"].mean():.4f}')
print(f'최대 유사도: {c14_c06["similarity"].max():.4f}')
