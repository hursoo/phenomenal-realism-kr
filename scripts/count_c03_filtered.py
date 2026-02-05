# -*- coding: utf-8 -*-
"""
노이즈 제외 후 C03 장의 정확한 쌍 개수 확인
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

# C03 섹션 추출
def extract_section(pid):
    if pd.isna(pid):
        return None
    match = re.match(r'(C03-S\d+)', str(pid))
    return match.group(1) if match else None

# C03 관련 쌍만 계산
c03_paras = para_1924[para_1924['pid'].str.startswith('C03', na=False)].copy()
c03_paras['section'] = c03_paras['pid'].apply(extract_section)

print('【C03 문단 유사도 ≥ 0.1 쌍 분석 (노이즈 제외)】')
print('=' * 70)

THRESHOLD = 0.1
results = []

for _, row1 in para_1915.iterrows():
    for _, row2 in c03_paras.iterrows():
        sim = jaccard_similarity(row1['tokens'], row2['tokens'])
        if sim >= THRESHOLD:
            if not is_noise_only(row1['tokens'], row2['tokens']):
                chapter_1915 = re.match(r'(C\d+)', row1['pid']).group(1)
                common = row1['tokens'] & row2['tokens']
                results.append({
                    'chapter_1915': chapter_1915,
                    'pid_1915': row1['pid'],
                    'pid_1924': row2['pid'],
                    'section_1924': row2['section'],
                    'similarity': sim,
                    'common_tokens': common
                })

df_results = pd.DataFrame(results)

# 섹션별 집계
print('\n【섹션별 분포】')
print('-' * 70)
for sec in ['C03-S01', 'C03-S02', 'C03-S03', 'C03-S04']:
    sec_df = df_results[df_results['section_1924'] == sec]
    print(f'{sec}: {len(sec_df)}개')

print()
print(f'C03 전체: {len(df_results)}개')

# S04 이외 상세
non_s04 = df_results[df_results['section_1924'] != 'C03-S04']
if len(non_s04) > 0:
    print('\n【S04 이외의 쌍 상세】')
    print('-' * 70)
    for _, row in non_s04.sort_values('similarity', ascending=False).iterrows():
        print(f"{row['pid_1915']} × {row['pid_1924']}")
        print(f"  유사도: {row['similarity']:.4f}")
        print(f"  공통 토큰: {row['common_tokens']}")
        print()

# S04 내 장별 분포
s04 = df_results[df_results['section_1924'] == 'C03-S04']
print('\n【S04 내 1915 장별 분포】')
print('-' * 70)
s04_by_ch = s04.groupby('chapter_1915').size().sort_values(ascending=False)
for ch, cnt in s04_by_ch.items():
    print(f'  {ch}: {cnt}개')
print(f'\n  S04 합계: {len(s04)}개')
