# -*- coding: utf-8 -*-
"""
C03-S04 항별 유사도 ≥ 0.1 쌍 재산출 (노이즈 제외)
"""
import pandas as pd
import numpy as np
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 노이즈 토큰
NOISE_TOKENS = {'第一', '第二', '第三', '第四', '第五', '第六', '第七', '第八', '第九', '第十',
                '其一', '其二', '其三', '其四', '其五',
                '如此', '如何', '所以', '然則', '故로', '卽是'}

# 데이터 로드
df_1915 = pd.read_excel('app/data/BK_IT_1915_PR_v1.3.xlsx')
df_1924 = pd.read_excel('app/data/BK_YD_1924_IY_v1.2.xlsx')

df_1915 = df_1915[df_1915['line_class'] == 'TEXT'].copy()
df_1924 = df_1924[df_1924['line_class'] == 'TEXT'].copy()

def extract_paragraph_id_1915(local_id):
    if pd.isna(local_id):
        return None
    match = re.match(r'(C\d+(?:-S\d+)?-P\d+)', str(local_id))
    if match:
        return match.group(1)
    match = re.match(r'(C\d+-P\d+)', str(local_id))
    if match:
        return match.group(1)
    return None

def extract_paragraph_id_1924(local_id):
    if pd.isna(local_id):
        return None
    match = re.match(r'(C\d+-S\d+(?:-I\d+)?-P\d+)', str(local_id))
    if match:
        return match.group(1)
    return None

def extract_hanja(text):
    if pd.isna(text):
        return set()
    return set(re.findall(r'[一-龥]{2,}', str(text)))

def jaccard_similarity(set1, set2):
    if not set1 or not set2:
        return 0.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0

def is_noise_only(set1, set2):
    common = set1 & set2
    if not common:
        return True
    meaningful = common - NOISE_TOKENS
    return len(meaningful) == 0

# 문단별 텍스트 집계
df_1915['pid'] = df_1915['local_id'].apply(extract_paragraph_id_1915)
df_1924['pid'] = df_1924['local_id'].apply(extract_paragraph_id_1924)

para_1915 = df_1915.groupby('pid')['kr_text'].apply(lambda x: ' '.join(x.dropna())).reset_index()
para_1924 = df_1924.groupby('pid')['kr_text'].apply(lambda x: ' '.join(x.dropna())).reset_index()

para_1915 = para_1915[para_1915['pid'].notna()]
para_1924 = para_1924[para_1924['pid'].notna()]

para_1915['tokens'] = para_1915['kr_text'].apply(extract_hanja)
para_1924['tokens'] = para_1924['kr_text'].apply(extract_hanja)

# C03-S04만 필터
c03s04_paras = para_1924[para_1924['pid'].str.startswith('C03-S04', na=False)].copy()

# 항 추출
def extract_item(pid):
    if pd.isna(pid):
        return '서두'
    match = re.search(r'C03-S04-(I\d+)', str(pid))
    if match:
        return match.group(1)
    return '서두'

c03s04_paras['item'] = c03s04_paras['pid'].apply(extract_item)

print('【C03-S04 항별 유사도 ≥ 0.1 쌍 분석 (노이즈 제외)】')
print('=' * 70)

THRESHOLD = 0.1
results = []

for _, row1 in para_1915.iterrows():
    for _, row2 in c03s04_paras.iterrows():
        sim = jaccard_similarity(row1['tokens'], row2['tokens'])
        if sim >= THRESHOLD:
            if not is_noise_only(row1['tokens'], row2['tokens']):
                chapter_1915 = re.match(r'(C\d+)', row1['pid']).group(1)
                common = row1['tokens'] & row2['tokens']
                results.append({
                    'chapter_1915': chapter_1915,
                    'pid_1915': row1['pid'],
                    'pid_1924': row2['pid'],
                    'item_1924': row2['item'],
                    'similarity': sim,
                    'common_tokens': common
                })

df_results = pd.DataFrame(results)

print(f'\nC03-S04 전체 유사도 ≥ 0.1 쌍 (노이즈 제외): {len(df_results)}개')
print()

# 항별 분포
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

print('【항별 분포】')
print('-' * 70)
print(f'{"항":<6} {"제목":<25} {"쌍 개수":<10} {"주요 참조 장"}')
print('-' * 70)

total = 0
for item, title in item_info:
    item_df = df_results[df_results['item_1924'] == item]
    cnt = len(item_df)
    total += cnt

    # 주요 참조 장
    if cnt > 0:
        ch_counts = item_df.groupby('chapter_1915').size().sort_values(ascending=False)
        main_refs = ', '.join([f'{ch}({c}개)' for ch, c in ch_counts.head(3).items()])
    else:
        main_refs = '-'

    print(f'{item:<6} {title:<25} {cnt:<10} {main_refs}')

print('-' * 70)
print(f'{"합계":<6} {"":<25} {total:<10}')

# 원본/차용 구분
print('\n【원본 vs 차용 구분】')
print('-' * 70)
original = ['I01', 'I03']
borrowed = ['서두', 'I02', 'I04', 'I05', 'I06', 'I07']

orig_cnt = df_results[df_results['item_1924'].isin(original)].shape[0]
borr_cnt = df_results[df_results['item_1924'].isin(borrowed)].shape[0]

print(f'독자적 항목 (I01, I03): {orig_cnt}개')
print(f'차용 항목 (서두, I02, I04-I07): {borr_cnt}개')
