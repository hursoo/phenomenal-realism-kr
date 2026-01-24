# -*- coding: utf-8 -*-
"""
C06-S06 (世界三大宗教의 差異点과 人乃天) 논리적 흐름 및 차용 지점 분석
"""
import pandas as pd
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 노이즈 토큰
NOISE_TOKENS = {'第一', '第二', '第三', '第四', '第五', '第六', '第七', '第八', '第九', '第十',
                '其一', '其二', '其三', '其四', '其五',
                '如此', '如何', '所以', '然則', '故로', '卽是'}

# 1924 텍스트 로드
df_1924 = pd.read_excel('app/data/BK_YD_1924_IY_v1.2.xlsx')
df_1924 = df_1924[df_1924['line_class'].isin(['TEXT', 'STRUCT'])]

# S06 문단 추출
s06 = df_1924[df_1924['local_id'].str.contains('C06-S06', na=False)].copy()

# 문단 ID 추출
def extract_para_id(local_id):
    match = re.match(r'(C06-S06(?:-I\d+)?-P\d+)', str(local_id))
    return match.group(1) if match else None

s06['para_id'] = s06['local_id'].apply(extract_para_id)

print('【C06-S06 世界三大宗教의 差異点과 人乃天 - 문단별 내용】')
print('=' * 80)

# 문단별 텍스트 집계
paras = s06.groupby('para_id').agg({
    'kr_text': lambda x: ' '.join(x.dropna().astype(str)),
    'local_id': 'first'
}).reset_index()

paras = paras[paras['para_id'].notna()].sort_values('para_id')

print(f'총 문단 수: {len(paras)}개')
print()

for _, row in paras.iterrows():
    pid = row['para_id']
    text = row['kr_text']
    print(f'【{pid}】')
    print(f'{text[:150]}...' if len(text) > 150 else text)
    print()

# 유사도 분석
print('=' * 80)
print('【유사도 ≥ 0.1 참조쌍 분석】')
print('=' * 80)

# 1915 텍스트 로드
df_1915 = pd.read_excel('app/data/BK_IT_1915_PR_v1.3.xlsx')
df_1915 = df_1915[df_1915['line_class'] == 'TEXT']

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

# 문단별 토큰
df_1915['pid'] = df_1915['local_id'].apply(extract_paragraph_id_1915)
para_1915 = df_1915.groupby('pid')['kr_text'].apply(lambda x: ' '.join(x.dropna().astype(str))).reset_index()
para_1915 = para_1915[para_1915['pid'].notna()]
para_1915['tokens'] = para_1915['kr_text'].apply(extract_hanja)

paras['tokens'] = paras['kr_text'].apply(extract_hanja)

# 유사도 계산
THRESHOLD = 0.1
results = []

for _, row1 in para_1915.iterrows():
    for _, row2 in paras.iterrows():
        sim = jaccard_similarity(row1['tokens'], row2['tokens'])
        if sim >= THRESHOLD:
            if not is_noise_only(row1['tokens'], row2['tokens']):
                chapter_1915 = re.match(r'(C\d+)', row1['pid']).group(1)
                common = row1['tokens'] & row2['tokens']
                results.append({
                    'chapter_1915': chapter_1915,
                    'pid_1915': row1['pid'],
                    'pid_1924': row2['para_id'],
                    'similarity': sim,
                    'common_tokens': common
                })

df_results = pd.DataFrame(results)

print(f'\nC06-S06 유사도 ≥ 0.1 쌍 (노이즈 제외): {len(df_results)}개')
print()

# 1915 장별 분포
print('【1915 장별 분포】')
print('-' * 60)
ch_counts = df_results.groupby('chapter_1915').size().sort_values(ascending=False)
for ch, cnt in ch_counts.items():
    print(f'  {ch}: {cnt}개')

# 문단별 참조 개수
print('\n【문단별 참조쌍 개수】')
print('-' * 60)
para_ref_counts = df_results.groupby('pid_1924').size()
for pid in sorted(paras['para_id'].unique()):
    if pid is None:
        continue
    cnt = para_ref_counts.get(pid, 0)
    marker = '★' if cnt >= 3 else ('●' if cnt > 0 else '○')
    print(f'{marker} {pid}: {cnt}개')

# 상세 분석
print('\n' + '=' * 80)
print('【문단별 참조 관계 상세】')
print('=' * 80)

def get_1915_text(pid):
    rows = df_1915[df_1915['local_id'].str.startswith(pid, na=False)]
    if len(rows) > 0:
        return ' '.join(rows['kr_text'].dropna().astype(str))
    return ''

for pid in sorted(paras['para_id'].unique()):
    if pid is None:
        continue

    text_1924 = paras[paras['para_id'] == pid]['kr_text'].values[0]
    refs = df_results[df_results['pid_1924'] == pid]

    print(f'\n{"="*80}')
    print(f'【{pid}】')
    print(f'{"="*80}')
    print(f'\n[1924 텍스트]')
    print(text_1924[:250] + ('...' if len(text_1924) > 250 else ''))

    if len(refs) > 0:
        print(f'\n[참조 관계] {len(refs)}개 쌍')
        for _, ref in refs.sort_values('similarity', ascending=False).head(3).iterrows():
            pid_1915 = ref['pid_1915']
            text_1915 = get_1915_text(pid_1915)
            tokens = ', '.join(sorted(ref['common_tokens']))[:60]
            print(f'\n  → {pid_1915} (유사도: {ref["similarity"]:.4f})')
            print(f'    공통 토큰: {tokens}...')
            print(f'    [1915] {text_1915[:150]}...' if len(text_1915) > 150 else f'    [1915] {text_1915}')
        if len(refs) > 3:
            print(f'\n    ... 외 {len(refs)-3}개 쌍')
    else:
        print(f'\n[참조 관계] 없음 (독자적 서술)')
