"""
공기어(共起語) 분석: '哲學'의 빈자리를 채운 대체어 탐구

분석 전략:
1. 1915 텍스트에서 '哲學' 포함 문단 추출
2. 해당 문단들의 공기 한자어 추출 → '哲學 문맥 어휘 집합'
3. 1924 텍스트에서 동일 공기어가 많이 나타나는 문단 탐색
4. 해당 문단에서 '哲學' 대신 어떤 단어가 높은 빈도로 등장하는지 확인
"""

import pandas as pd
import re
from collections import Counter, defaultdict
import json

# 데이터 로드
df_1915 = pd.read_excel('app/data/BK_IT_1915_PR_v1.3.xlsx')
df_1924 = pd.read_excel('app/data/BK_YD_1924_IY_v1.2.xlsx')

# 분석 대상 필터링
def filter_text_rows(df):
    mask = (
        df['line_class'].isin(['TEXT', 'STRUCT']) &
        ~df['structure_id'].isin(['TOC', 'ROOT'])
    )
    return df[mask].copy()

df_1915_filtered = filter_text_rows(df_1915)
df_1924_filtered = filter_text_rows(df_1924)

# 한자어 추출 함수
def extract_hanja(text):
    if pd.isna(text):
        return []
    return re.findall(r'[一-龥]{2,}', str(text))

# 문단 ID 추출 (문장 → 문단 집계용)
def get_paragraph_id(local_id):
    """local_id에서 문단 ID 추출 (마지막 S## 제거)"""
    parts = str(local_id).split('-')
    # 마지막이 S##이면 제거
    if parts and parts[-1].startswith('S') and len(parts[-1]) == 3:
        return '-'.join(parts[:-1])
    return local_id

# 문단 단위로 텍스트 집계
def aggregate_paragraphs(df):
    df = df.copy()
    df['para_id'] = df['local_id'].apply(get_paragraph_id)
    para_texts = df.groupby('para_id')['kr_text'].apply(lambda x: ' '.join(x.dropna())).reset_index()
    para_texts.columns = ['para_id', 'full_text']
    para_texts['tokens'] = para_texts['full_text'].apply(extract_hanja)
    return para_texts

print("=== 문단 단위 집계 중 ===")
para_1915 = aggregate_paragraphs(df_1915_filtered)
para_1924 = aggregate_paragraphs(df_1924_filtered)
print(f"1915 문단 수: {len(para_1915)}")
print(f"1924 문단 수: {len(para_1924)}")

# ============================================================
# 1단계: 1915 텍스트에서 '哲學' 포함 문단 추출
# ============================================================
print("\n=== 1단계: '哲學' 포함 문단 추출 ===")

def contains_philosophy(tokens):
    """'哲學' 또는 '哲學' 포함 복합어가 있는지 확인"""
    for token in tokens:
        if '哲學' in token:
            return True
    return False

para_1915['has_philosophy'] = para_1915['tokens'].apply(contains_philosophy)
philosophy_paras_1915 = para_1915[para_1915['has_philosophy']]
print(f"'哲學' 포함 문단 수: {len(philosophy_paras_1915)}")

# ============================================================
# 2단계: '哲學' 공기어 집합 추출
# ============================================================
print("\n=== 2단계: '哲學' 공기어 추출 ===")

# '哲學' 포함 문단에서 모든 한자어 추출 (哲學 자체 제외)
cooccurrence_counter = Counter()
for tokens in philosophy_paras_1915['tokens']:
    for token in tokens:
        if '哲學' not in token:  # 哲學 및 복합어 제외
            cooccurrence_counter[token] += 1

# 상위 50개 공기어
top_cooccurrences = cooccurrence_counter.most_common(50)
print("\n'哲學' 공기어 상위 30개:")
for i, (word, count) in enumerate(top_cooccurrences[:30], 1):
    print(f"  {i:2}. {word}: {count}회")

# 공기어 집합 (상위 100개)
philosophy_context_words = set([w for w, c in cooccurrence_counter.most_common(100)])
print(f"\n공기어 집합 크기: {len(philosophy_context_words)}개")

# ============================================================
# 3단계: 1924 텍스트에서 '哲學 문맥'과 유사한 문단 탐색
# ============================================================
print("\n=== 3단계: 1924 텍스트에서 유사 문맥 탐색 ===")

def count_context_overlap(tokens, context_set):
    """문단의 토큰 중 공기어 집합과 겹치는 개수"""
    return len(set(tokens) & context_set)

para_1924['context_overlap'] = para_1924['tokens'].apply(
    lambda t: count_context_overlap(t, philosophy_context_words)
)
para_1924['has_philosophy'] = para_1924['tokens'].apply(contains_philosophy)

# 공기어 중첩이 높은 문단 (상위 50개)
similar_context_paras = para_1924.nlargest(50, 'context_overlap')

print(f"\n공기어 중첩 상위 10개 문단:")
for _, row in similar_context_paras.head(10).iterrows():
    has_phil = "있음" if row['has_philosophy'] else "없음"
    print(f"  {row['para_id']}: 중첩 {row['context_overlap']}개, 哲學 {has_phil}")

# ============================================================
# 4단계: '哲學 문맥' 문단에서 대체어 후보 탐색
# ============================================================
print("\n=== 4단계: 대체어 후보 탐색 ===")

# 공기어 중첩이 5개 이상인 문단에서 고빈도 단어 추출
high_overlap_paras = para_1924[para_1924['context_overlap'] >= 5]
print(f"공기어 중첩 5개 이상 문단 수: {len(high_overlap_paras)}")

# 해당 문단들의 전체 토큰 빈도
substitute_counter = Counter()
for tokens in high_overlap_paras['tokens']:
    for token in tokens:
        if '哲學' not in token:  # 哲學 제외
            substitute_counter[token] += 1

# 상위 30개 후보
print("\n'哲學 문맥' 문단 내 고빈도 단어 (대체어 후보):")
for i, (word, count) in enumerate(substitute_counter.most_common(30), 1):
    # 공기어 집합에도 있는지 표시
    in_context = "◎" if word in philosophy_context_words else "  "
    print(f"  {i:2}. {in_context} {word}: {count}회")

# ============================================================
# 5단계: '哲學' 있는 문단 vs 없는 문단 비교 (1924)
# ============================================================
print("\n=== 5단계: 1924 텍스트 내 비교 분석 ===")

# 공기어 중첩이 높지만 '哲學'이 없는 문단
high_overlap_no_phil = para_1924[
    (para_1924['context_overlap'] >= 5) &
    (~para_1924['has_philosophy'])
]
print(f"공기어 중첩 ≥5 & 哲學 없음: {len(high_overlap_no_phil)}개 문단")

# 이 문단들에서 고빈도 단어
no_phil_counter = Counter()
for tokens in high_overlap_no_phil['tokens']:
    for token in tokens:
        no_phil_counter[token] += 1

print("\n'哲學' 없이 철학적 문맥을 가진 문단의 고빈도 단어:")
for i, (word, count) in enumerate(no_phil_counter.most_common(20), 1):
    print(f"  {i:2}. {word}: {count}회")

# ============================================================
# 6단계: 특정 공기어 조합별 분석
# ============================================================
print("\n=== 6단계: 핵심 공기어 조합별 분석 ===")

# 철학의 핵심 공기어 (유물론/유심론/실재 등)
core_philosophy_words = {'唯物論', '唯心論', '實在', '眞理', '認識', '理性'}

def has_core_words(tokens, core_set):
    return len(set(tokens) & core_set) >= 2

para_1924['has_core_context'] = para_1924['tokens'].apply(
    lambda t: has_core_words(t, core_philosophy_words)
)

core_context_paras = para_1924[para_1924['has_core_context']]
print(f"핵심 공기어 2개 이상 포함 문단: {len(core_context_paras)}개")

# 해당 문단들의 고빈도 단어
core_counter = Counter()
for tokens in core_context_paras['tokens']:
    for token in tokens:
        if token not in core_philosophy_words:
            core_counter[token] += 1

print("\n핵심 철학 문맥(唯物論/唯心論/實在 등) 문단의 고빈도 단어:")
for i, (word, count) in enumerate(core_counter.most_common(20), 1):
    phil_mark = "×" if '哲學' in word else " "
    print(f"  {i:2}. {phil_mark} {word}: {count}회")

# ============================================================
# 결과 저장
# ============================================================
print("\n=== 결과 저장 ===")

# 공기어 목록 저장
cooccurrence_df = pd.DataFrame(top_cooccurrences, columns=['word', 'count'])
cooccurrence_df.to_csv('data/analysis/philosophy_cooccurrence_1915.csv',
                       index=False, encoding='utf-8-sig')

# 대체어 후보 저장
substitute_df = pd.DataFrame(substitute_counter.most_common(50),
                            columns=['word', 'count'])
substitute_df.to_csv('data/analysis/philosophy_substitute_candidates_1924.csv',
                    index=False, encoding='utf-8-sig')

# 상세 분석 결과
analysis_result = {
    'philosophy_paragraphs_1915': len(philosophy_paras_1915),
    'context_words_count': len(philosophy_context_words),
    'high_overlap_paragraphs_1924': len(high_overlap_paras),
    'core_context_paragraphs_1924': len(core_context_paras),
    'top_cooccurrences': top_cooccurrences[:30],
    'top_substitutes': substitute_counter.most_common(30)
}

with open('data/analysis/philosophy_cooccurrence_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(analysis_result, f, ensure_ascii=False, indent=2)

print("저장 완료:")
print("  - data/analysis/philosophy_cooccurrence_1915.csv")
print("  - data/analysis/philosophy_substitute_candidates_1924.csv")
print("  - data/analysis/philosophy_cooccurrence_analysis.json")
