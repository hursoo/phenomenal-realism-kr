# -*- coding: utf-8 -*-
"""
C03-S04 항별 유사도 분석 결과 엑셀 저장
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

def extract_item(pid):
    if pd.isna(pid):
        return '서두'
    match = re.search(r'C03-S04-(I\d+)', str(pid))
    if match:
        return match.group(1)
    return '서두'

c03s04_paras['item'] = c03s04_paras['pid'].apply(extract_item)

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
                    'common_tokens': ', '.join(sorted(common))
                })

df_results = pd.DataFrame(results)

# 표 1: 항별 요약
item_info = [
    ('서두', '(원리상/응용상 구분)', '독자적'),
    ('I01', '實現思想과 人乃天', '독자적'),
    ('I02', '實在와 人乃天', '차용'),
    ('I03', '汎神觀과 人乃天', '독자적'),
    ('I04', '生命과 人乃天', '차용'),
    ('I05', '意識과 人乃天', '차용'),
    ('I06', '靈魂과 人乃天', '차용'),
    ('I07', '進化와 人乃天', '차용'),
]

summary_data = []
for item, title, nature in item_info:
    item_df = df_results[df_results['item_1924'] == item]
    cnt = len(item_df)

    if cnt > 0:
        ch_counts = item_df.groupby('chapter_1915').size().sort_values(ascending=False)
        main_refs = ', '.join([f'{ch}({c})' for ch, c in ch_counts.head(3).items()])
    else:
        main_refs = '-'

    summary_data.append({
        '항': item,
        '제목': title,
        '참조쌍 개수': cnt,
        '주요 참조 장': main_refs,
        '성격': nature
    })

df_summary = pd.DataFrame(summary_data)

# 표 2: C03 전체 섹션별 분포
c03_section_data = [
    {'섹션': 'C03-S01', '제목': '天道敎의 宗旨', '참조쌍 개수': 0},
    {'섹션': 'C03-S02', '제목': '人乃天의 發源', '참조쌍 개수': 0},
    {'섹션': 'C03-S03', '제목': '人乃天의 信仰', '참조쌍 개수': 3},
    {'섹션': 'C03-S04', '제목': '人乃天의 哲理', '참조쌍 개수': 52},
]
df_c03_sections = pd.DataFrame(c03_section_data)

# 표 3: 상세 쌍 목록
df_pairs = df_results[['pid_1915', 'pid_1924', 'item_1924', 'chapter_1915', 'similarity', 'common_tokens']].copy()
df_pairs = df_pairs.sort_values(['item_1924', 'similarity'], ascending=[True, False])
df_pairs.columns = ['1915 문단ID', '1924 문단ID', '항', '1915 장', '유사도', '공통 토큰']

# 엑셀 저장
output_path = 'app/data/C03-S04_참조분석.xlsx'
with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
    df_summary.to_excel(writer, sheet_name='항별 요약', index=False)
    df_c03_sections.to_excel(writer, sheet_name='C03 섹션별 분포', index=False)
    df_pairs.to_excel(writer, sheet_name='상세 쌍 목록', index=False)

print(f'저장 완료: {output_path}')
print()
print('【항별 요약】')
print(df_summary.to_string(index=False))
print()
print(f'총 참조쌍: {len(df_results)}개')
