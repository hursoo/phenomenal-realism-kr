# -*- coding: utf-8 -*-
"""
C06 (인내천의 雜感) 구조 및 참조 분포 분석
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

df_1915_text = df_1915[df_1915['line_class'] == 'TEXT'].copy()
df_1924_text = df_1924[df_1924['line_class'].isin(['TEXT', 'STRUCT'])].copy()

# C06 구조 파악
c06 = df_1924_text[df_1924_text['local_id'].str.startswith('C06', na=False)].copy()

print('【C06 인내천의 雜感 - 구조 분석】')
print('=' * 80)

# 섹션 추출
def extract_section(local_id):
    if pd.isna(local_id):
        return None
    match = re.match(r'(C06-S\d+)', str(local_id))
    return match.group(1) if match else None

def extract_item(local_id):
    if pd.isna(local_id):
        return None
    match = re.search(r'C06-S\d+-(I\d+)', str(local_id))
    return match.group(1) if match else None

c06['section'] = c06['local_id'].apply(extract_section)
c06['item'] = c06['local_id'].apply(extract_item)

# 섹션별 구조
sections = c06.groupby('section').agg({
    'local_id': 'count',
    'item': lambda x: x.dropna().nunique()
}).reset_index()
sections.columns = ['섹션', '행 수', '항 수']

print('\n【섹션별 구조】')
print('-' * 60)

# 섹션별 제목 추출 (STRUCT에서)
df_struct = df_1924[df_1924['line_class'] == 'STRUCT']
for sec in sorted(c06['section'].dropna().unique()):
    sec_struct = df_struct[df_struct['local_id'].str.startswith(sec, na=False)]
    title = ''
    if len(sec_struct) > 0:
        first_text = sec_struct.iloc[0]['kr_text']
        if pd.notna(first_text):
            title = str(first_text)[:30]

    row_count = len(c06[c06['section'] == sec])
    item_count = c06[c06['section'] == sec]['item'].dropna().nunique()

    print(f'{sec}: {title}')
    print(f'       행 수: {row_count}, 항 수: {item_count}')

    # 항 목록
    items = c06[c06['section'] == sec]['item'].dropna().unique()
    if len(items) > 0:
        print(f'       항: {", ".join(sorted(items))}')
    print()

# 유사도 분석
print('\n' + '=' * 80)
print('【C06 유사도 ≥ 0.1 참조쌍 분석 (노이즈 제외)】')
print('=' * 80)

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
df_1915_text['pid'] = df_1915_text['local_id'].apply(extract_paragraph_id_1915)
df_1924_text['pid'] = df_1924_text['local_id'].apply(extract_paragraph_id_1924)

para_1915 = df_1915_text.groupby('pid')['kr_text'].apply(lambda x: ' '.join(x.dropna().astype(str))).reset_index()
para_1924 = df_1924_text.groupby('pid')['kr_text'].apply(lambda x: ' '.join(x.dropna().astype(str))).reset_index()

para_1915 = para_1915[para_1915['pid'].notna()]
para_1924 = para_1924[para_1924['pid'].notna()]

para_1915['tokens'] = para_1915['kr_text'].apply(extract_hanja)
para_1924['tokens'] = para_1924['kr_text'].apply(extract_hanja)

# C06만 필터
c06_paras = para_1924[para_1924['pid'].str.startswith('C06', na=False)].copy()
c06_paras['section'] = c06_paras['pid'].apply(lambda x: re.match(r'(C06-S\d+)', str(x)).group(1) if re.match(r'(C06-S\d+)', str(x)) else None)

THRESHOLD = 0.1
results = []

for _, row1 in para_1915.iterrows():
    for _, row2 in c06_paras.iterrows():
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

print(f'\nC06 전체 유사도 ≥ 0.1 쌍 (노이즈 제외): {len(df_results)}개')
print()

# 섹션별 분포
print('【섹션별 분포】')
print('-' * 60)
section_counts = df_results.groupby('section_1924').size().sort_values(ascending=False)
for sec, cnt in section_counts.items():
    # 주요 참조 장
    sec_df = df_results[df_results['section_1924'] == sec]
    ch_counts = sec_df.groupby('chapter_1915').size().sort_values(ascending=False)
    main_refs = ', '.join([f'{ch}({c})' for ch, c in ch_counts.head(3).items()])
    print(f'{sec}: {cnt}개  ← {main_refs}')

print()
print('【1915 장별 분포 (C06 전체)】')
print('-' * 60)
ch_counts = df_results.groupby('chapter_1915').size().sort_values(ascending=False)
for ch, cnt in ch_counts.items():
    print(f'  {ch}: {cnt}개')

# 엑셀 저장
print('\n' + '=' * 80)
print('엑셀 저장 중...')

# 섹션별 요약
section_summary = []
for sec in sorted(c06_paras['section'].dropna().unique()):
    sec_df = df_results[df_results['section_1924'] == sec]
    cnt = len(sec_df)
    if cnt > 0:
        ch_counts = sec_df.groupby('chapter_1915').size().sort_values(ascending=False)
        main_refs = ', '.join([f'{ch}({c})' for ch, c in ch_counts.head(3).items()])
    else:
        main_refs = '-'
    section_summary.append({
        '섹션': sec,
        '참조쌍 개수': cnt,
        '주요 참조 장': main_refs
    })

df_section_summary = pd.DataFrame(section_summary)

# 상세 쌍 목록
df_pairs = df_results[['pid_1915', 'pid_1924', 'section_1924', 'chapter_1915', 'similarity']].copy()
df_pairs['common_tokens'] = df_results['common_tokens'].apply(lambda x: ', '.join(sorted(x)) if x else '')
df_pairs = df_pairs.sort_values(['section_1924', 'similarity'], ascending=[True, False])
df_pairs.columns = ['1915 문단ID', '1924 문단ID', '섹션', '1915 장', '유사도', '공통 토큰']

output_path = 'app/data/C06_참조분석.xlsx'
with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
    df_section_summary.to_excel(writer, sheet_name='섹션별 요약', index=False)
    df_pairs.to_excel(writer, sheet_name='상세 쌍 목록', index=False)

print(f'저장 완료: {output_path}')
