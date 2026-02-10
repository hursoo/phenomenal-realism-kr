"""
의미장 분석 재현: 발표문 35쪽 '26개 문단' 도출 과정 검증
"""
import pandas as pd
import re
import sys
import io
from collections import Counter

# UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 데이터 로드
df_1915 = pd.read_excel('data/3_corpus/BK_IT_1915_PR_v1.3.xlsx')
df_1924 = pd.read_excel('data/3_corpus/BK_YD_1924_IY_v1.2.xlsx')

# 분석 대상 필터링
def filter_text_rows(df):
    mask = (
        df['line_class'].isin(['TEXT', 'STRUCT']) &
        ~df['structure_id'].isin(['TOC', 'ROOT'])
    )
    return df[mask].copy()

df_1915_f = filter_text_rows(df_1915)
df_1924_f = filter_text_rows(df_1924)

def extract_hanja(text):
    if pd.isna(text):
        return []
    return re.findall(r'[一-龥]{2,}', str(text))

def get_paragraph_id(local_id):
    parts = str(local_id).split('-')
    if parts and parts[-1].startswith('S') and len(parts[-1]) == 3:
        return '-'.join(parts[:-1])
    return local_id

def aggregate_paragraphs(df):
    df = df.copy()
    df['para_id'] = df['local_id'].apply(get_paragraph_id)
    para_texts = df.groupby('para_id')['kr_text'].apply(lambda x: ' '.join(x.dropna())).reset_index()
    para_texts.columns = ['para_id', 'full_text']
    para_texts['tokens'] = para_texts['full_text'].apply(extract_hanja)
    para_texts['token_set'] = para_texts['tokens'].apply(set)
    return para_texts

para_1915 = aggregate_paragraphs(df_1915_f)
para_1924 = aggregate_paragraphs(df_1924_f)
print(f'1915 문단: {len(para_1915)}, 1924 문단: {len(para_1924)}')

# 哲學 포함 문단
def contains_philosophy(token_set):
    return any('哲學' in t for t in token_set)

para_1915['has_phil'] = para_1915['token_set'].apply(contains_philosophy)
phil_paras = para_1915[para_1915['has_phil']]
print(f'1915 哲學 포함 문단: {len(phil_paras)}')

n_phil = len(phil_paras)
n_all = len(para_1915)

# 공기어 문단 빈도 (각 단어가 哲學 문단 몇 개에 출현하는지)
phil_word_counts = Counter()
for ts in phil_paras['token_set']:
    for t in ts:
        if '哲學' not in t:
            phil_word_counts[t] += 1

# 전체 문단에서의 문단 빈도
all_word_counts = Counter()
for ts in para_1915['token_set']:
    for t in ts:
        all_word_counts[t] += 1

# 의미장 기준: 동반율 >= 15% AND 배율 >= 1.5x
semantic_field = []
for word, phil_count in phil_word_counts.items():
    companionship = phil_count / n_phil
    all_rate = all_word_counts[word] / n_all
    if all_rate > 0:
        ratio = companionship / all_rate
    else:
        ratio = float('inf')

    if companionship >= 0.15 and ratio >= 1.5:
        semantic_field.append((word, companionship, all_rate, ratio, phil_count))

semantic_field.sort(key=lambda x: -x[3])
print(f'\n=== 의미장 단어: {len(semantic_field)}개 ===')
for w, comp, all_r, rat, cnt in semantic_field:
    print(f'  {w}: 동반율 {comp:.1%} ({cnt}/{n_phil}), 전체 {all_r:.1%}, 배율 {rat:.1f}x')

sf_words = set(w for w, _, _, _, _ in semantic_field)

# 발표문에 명시된 19개 단어
presentation_19 = {'最後', '態度', '立場', '傾向', '範圍', '問題', '印度', '西洋',
                   '思想', '主張', '硏究', '解釋', '方面', '目的', '結果', '如何',
                   '次第', '生命', '世界'}

print(f'\n발표문 19개와 비교:')
print(f'  일치:      {sorted(sf_words & presentation_19)}')
print(f'  재현에만:  {sorted(sf_words - presentation_19)}')
print(f'  발표문에만: {sorted(presentation_19 - sf_words)}')

# 1924 문단에서 의미장 단어 3개 이상 동시 출현 문단 찾기
# (발표문 19개 사용)
use_words = presentation_19

para_1924['sf_overlap'] = para_1924['token_set'].apply(
    lambda ts: len(ts & use_words)
)
para_1924['has_phil'] = para_1924['token_set'].apply(contains_philosophy)
para_1924['sf_matched'] = para_1924['token_set'].apply(
    lambda ts: sorted(ts & use_words)
)

matched = para_1924[para_1924['sf_overlap'] >= 3].copy()
print(f'\n=== 의미장 3개 이상 동시 출현 문단: {len(matched)}개 ===')
print(f'  哲學 있음: {matched["has_phil"].sum()}개')
print(f'  哲學 없음: {(~matched["has_phil"]).sum()}개')

print(f'\n--- 26개 문단 목록 ---')
for _, row in matched.sort_values('sf_overlap', ascending=False).iterrows():
    phil_mark = "[哲學O]" if row['has_phil'] else "[哲學X]"
    print(f'  {row["para_id"]:30s}  중첩 {row["sf_overlap"]}개  {phil_mark}  {row["sf_matched"]}')

# 대표 사례 3개 출력 (哲學 없는 문단 중 중첩 수 상위)
print(f'\n=== 대표 사례 (哲學 없는 문단 중 의미장 중첩 상위 5개) ===')
no_phil_matched = matched[~matched['has_phil']].sort_values('sf_overlap', ascending=False)
for i, (_, row) in enumerate(no_phil_matched.head(5).iterrows(), 1):
    print(f'\n{"="*80}')
    print(f'사례 {i}: {row["para_id"]} (의미장 단어 {row["sf_overlap"]}개)')
    print(f'매칭 의미장 단어: {row["sf_matched"]}')
    print(f'{"="*80}')
    text = row['full_text']
    if len(text) > 800:
        print(f'원문(앞 800자):\n{text[:800]}...')
    else:
        print(f'원문:\n{text}')
    token_freq = Counter(row['tokens'])
    top_tokens = token_freq.most_common(15)
    print(f'\n고빈도 한자어: {top_tokens}')

# 哲學 없는 24개 문단의 고빈도 단어
print(f'\n=== 哲學 없는 문단들의 고빈도 고유 단어 ===')
no_phil_counter = Counter()
for tokens in no_phil_matched['tokens']:
    for t in tokens:
        no_phil_counter[t] += 1

for i, (w, c) in enumerate(no_phil_counter.most_common(20), 1):
    print(f'  {i:2}. {w}: {c}회')
