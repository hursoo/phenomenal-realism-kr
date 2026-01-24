# -*- coding: utf-8 -*-
"""
C03-S04-I02 (實在와 人乃天) 논리적 흐름 및 차용 지점 분석
"""
import pandas as pd
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 1924 텍스트 로드
df_1924 = pd.read_excel('app/data/BK_YD_1924_IY_v1.2.xlsx')
df_1924 = df_1924[df_1924['line_class'].isin(['TEXT', 'STRUCT'])]

# I02 문단 추출
i02 = df_1924[df_1924['local_id'].str.contains('C03-S04-I02', na=False)].copy()

# 문단 ID 추출
def extract_para_id(local_id):
    match = re.match(r'(C03-S04-I02-P\d+)', str(local_id))
    return match.group(1) if match else None

i02['para_id'] = i02['local_id'].apply(extract_para_id)

print('【C03-S04-I02 實在와 人乃天 - 문단별 내용】')
print('=' * 80)

# 문단별 텍스트 집계
paras = i02.groupby('para_id').agg({
    'kr_text': lambda x: ' '.join(x.dropna().astype(str)),
    'local_id': 'first'
}).reset_index()

paras = paras.sort_values('para_id')

for _, row in paras.iterrows():
    pid = row['para_id']
    text = row['kr_text']
    print(f'\n【{pid}】')
    print(f'{text[:200]}...' if len(text) > 200 else text)

print('\n' + '=' * 80)

# 참조 분석 결과 로드
df_refs = pd.read_excel('app/data/C03-S04_참조분석.xlsx', sheet_name='상세 쌍 목록')
i02_refs = df_refs[df_refs['항'] == 'I02'].copy()

print('\n【I02 참조쌍 (15개)】')
print('-' * 80)
print(f"{'1924 문단':<25} {'1915 문단':<15} {'유사도':<10} {'공통 토큰'}")
print('-' * 80)

for _, row in i02_refs.sort_values('1924 문단ID').iterrows():
    print(f"{row['1924 문단ID']:<25} {row['1915 문단ID']:<15} {row['유사도']:<10.4f} {row['공통 토큰'][:40]}...")

# 1915 텍스트도 로드하여 대응 내용 확인
df_1915 = pd.read_excel('app/data/BK_IT_1915_PR_v1.3.xlsx')
df_1915 = df_1915[df_1915['line_class'] == 'TEXT']

def get_1915_text(pid):
    rows = df_1915[df_1915['local_id'].str.startswith(pid, na=False)]
    if len(rows) > 0:
        return ' '.join(rows['kr_text'].dropna().astype(str))
    return ''

print('\n' + '=' * 80)
print('\n【1924 문단별 참조 관계 상세】')
print('=' * 80)

# I02의 각 문단에 대해 참조 관계 표시
for pid in sorted(paras['para_id'].unique()):
    if pid is None:
        continue

    # 해당 문단의 1924 텍스트
    text_1924 = paras[paras['para_id'] == pid]['kr_text'].values[0]

    # 해당 문단의 참조쌍
    refs = i02_refs[i02_refs['1924 문단ID'] == pid]

    print(f'\n{"="*80}')
    print(f'【{pid}】')
    print(f'{"="*80}')
    print(f'\n[1924 텍스트]')
    print(text_1924[:300] + ('...' if len(text_1924) > 300 else ''))

    if len(refs) > 0:
        print(f'\n[참조 관계] {len(refs)}개 쌍')
        for _, ref in refs.iterrows():
            pid_1915 = ref['1915 문단ID']
            text_1915 = get_1915_text(pid_1915)
            print(f'\n  → {pid_1915} (유사도: {ref["유사도"]:.4f})')
            print(f'    공통 토큰: {ref["공통 토큰"]}')
            print(f'    [1915 텍스트] {text_1915[:200]}...' if len(text_1915) > 200 else f'    [1915 텍스트] {text_1915}')
    else:
        print(f'\n[참조 관계] 없음 (독자적 서술)')
