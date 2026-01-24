"""
'哲學' 문장 구조 분석: 술어 패턴 매칭을 통한 대체어 탐색

분석 전략:
1. 1915에서 '哲學'이 포함된 문장 추출
2. 해당 문장의 술어/서술 패턴 분석
3. 1924에서 동일 술어를 사용하는 문장 탐색
4. 해당 문장에서 '哲學' 대신 어떤 단어가 주어 위치에 있는지 확인
"""

import pandas as pd
import re
from collections import Counter, defaultdict
import sys
import io

# 인코딩 문제 해결
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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

df_1915_text = filter_text_rows(df_1915)
df_1924_text = filter_text_rows(df_1924)

# 한자어 추출
def extract_hanja(text):
    if pd.isna(text):
        return []
    return re.findall(r'[一-龥]{2,}', str(text))

# ============================================================
# 1단계: '哲學'이 포함된 문장 추출 및 문맥 분석
# ============================================================
print("=== 1단계: '哲學' 포함 문장 분석 ===")

philosophy_sentences = df_1915_text[
    df_1915_text['kr_text'].str.contains('哲學', na=False)
]
print(f"'哲學' 포함 문장 수: {len(philosophy_sentences)}")

# '哲學'과 함께 등장하는 서술어/동사구 패턴 추출
# 일본어 동사 어미 패턴
verb_patterns = [
    r'哲學[はがをにで]*([一-龥]{2,})[るたすでき]',  # 일본어 동사
    r'哲學[이가은는을의]?\s*([一-龥]{2,})',  # 한국어 조사 후 한자어
]

# 주요 서술어 패턴 수동 추출
predicates_with_philosophy = []

for text in philosophy_sentences['kr_text']:
    if pd.isna(text):
        continue
    text = str(text)

    # '哲學' 주변 한자어 추출 (앞뒤 문맥)
    matches = re.findall(r'哲學[^一-龥]*([一-龥]{2,})', text)
    predicates_with_philosophy.extend(matches)

    # '哲學'이 주어일 때 서술어 패턴
    if '哲學は' in text or '哲學が' in text or '哲學의' in text or '哲學이' in text:
        following = re.findall(r'哲學[はがの이의][^一-龥]*([一-龥]{2,})', text)
        predicates_with_philosophy.extend(following)

predicate_counter = Counter(predicates_with_philosophy)
print("\n'哲學' 뒤에 자주 등장하는 한자어 (서술어/목적어 후보):")
for word, count in predicate_counter.most_common(20):
    print(f"  {word}: {count}회")

# ============================================================
# 2단계: 핵심 서술어와 함께하는 주어 분석
# ============================================================
print("\n=== 2단계: 핵심 서술어별 주어 분석 ===")

# 철학과 관련된 핵심 서술어들
key_predicates = ['檢討', '發達', '要求', '必要', '硏究', '根據', '認識', '解決', '眞理']

def find_subjects_for_predicate(df, predicate):
    """특정 서술어가 포함된 문장에서 주어 후보 추출"""
    sentences = df[df['kr_text'].str.contains(predicate, na=False)]
    subjects = []
    for text in sentences['kr_text']:
        if pd.isna(text):
            continue
        # 서술어 앞의 한자어들을 주어 후보로 추출
        text = str(text)
        # 서술어 앞에 오는 한자어
        pattern = rf'([一-龥]{{2,}})[はがのいの이가은는]*[^一-龥]*{predicate}'
        matches = re.findall(pattern, text)
        subjects.extend(matches)
    return Counter(subjects)

print("\n핵심 서술어별 주어 비교 (1915 vs 1924):")
print("-" * 60)

for pred in key_predicates:
    subj_1915 = find_subjects_for_predicate(df_1915_text, pred)
    subj_1924 = find_subjects_for_predicate(df_1924_text, pred)

    if subj_1915 or subj_1924:
        print(f"\n서술어: {pred}")

        # 1915에서 '哲學' 포함 여부
        phil_in_1915 = subj_1915.get('哲學', 0)
        top_1915 = subj_1915.most_common(5)

        # 1924에서 상위 주어
        top_1924 = subj_1924.most_common(5)

        print(f"  1915: {top_1915[:3]} (哲學: {phil_in_1915}회)")
        print(f"  1924: {top_1924[:3]}")

# ============================================================
# 3단계: '哲學' vs 대체어 후보 문맥 비교
# ============================================================
print("\n\n=== 3단계: '哲學' vs 대체어 문맥 비교 ===")

# 대체어 후보 목록
substitute_candidates = ['人乃天', '眞理', '天道', '進化']

# 각 후보가 등장하는 문장에서의 공기어 비교
for candidate in substitute_candidates:
    print(f"\n--- '{candidate}' 분석 ---")

    # 1924에서 해당 단어 포함 문장
    candidate_sentences = df_1924_text[
        df_1924_text['kr_text'].str.contains(candidate, na=False)
    ]
    print(f"'{candidate}' 포함 문장 수: {len(candidate_sentences)}")

    # 공기어 추출
    cooc = Counter()
    for text in candidate_sentences['kr_text']:
        tokens = extract_hanja(str(text))
        for token in tokens:
            if token != candidate:
                cooc[token] += 1

    # 상위 공기어
    print(f"공기어 상위 10개: {cooc.most_common(10)}")

# ============================================================
# 4단계: 핵심 공기어 조합 분석
# ============================================================
print("\n\n=== 4단계: 유물론/유심론/실재 문맥 분석 ===")

# 1915: 哲學 + 唯物論/唯心論 동시 출현
core_context_1915 = df_1915_text[
    df_1915_text['kr_text'].str.contains('哲學', na=False) &
    (df_1915_text['kr_text'].str.contains('唯物論', na=False) |
     df_1915_text['kr_text'].str.contains('唯心論', na=False) |
     df_1915_text['kr_text'].str.contains('實在', na=False))
]
print(f"1915 '哲學' + (唯物論/唯心論/實在) 동시 출현: {len(core_context_1915)}개 문장")

# 1924: 唯物論/唯心論/實在 출현 (哲學 제외)
core_context_1924 = df_1924_text[
    ~df_1924_text['kr_text'].str.contains('哲學', na=False) &
    (df_1924_text['kr_text'].str.contains('唯物論', na=False) |
     df_1924_text['kr_text'].str.contains('唯心論', na=False) |
     df_1924_text['kr_text'].str.contains('實在', na=False))
]
print(f"1924 (唯物論/唯心論/實在) 출현 & '哲學' 부재: {len(core_context_1924)}개 문장")

# 해당 문장들의 고빈도 단어
core_words_1924 = Counter()
for text in core_context_1924['kr_text']:
    tokens = extract_hanja(str(text))
    for token in tokens:
        if '哲學' not in token and token not in ['唯物論', '唯心論', '實在']:
            core_words_1924[token] += 1

print("\n'唯物論/唯心論/實在' 문맥에서 '哲學' 없이 등장하는 고빈도 단어:")
for word, count in core_words_1924.most_common(15):
    print(f"  {word}: {count}회")

# ============================================================
# 5단계: 샘플 문장 비교
# ============================================================
print("\n\n=== 5단계: 샘플 문장 비교 ===")

print("\n[1915] '哲學' + '唯物論/唯心論' 문장 샘플:")
for i, (_, row) in enumerate(core_context_1915.head(3).iterrows()):
    text = str(row['kr_text'])[:100]
    print(f"  {i+1}. {row['local_id']}: {text}...")

print("\n[1924] '唯物論/唯心論' + '哲學 부재' 문장 샘플:")
for i, (_, row) in enumerate(core_context_1924.head(3).iterrows()):
    text = str(row['kr_text'])[:100]
    print(f"  {i+1}. {row['local_id']}: {text}...")

# ============================================================
# 결과 저장
# ============================================================
print("\n=== 결과 저장 ===")

# 핵심 결과 정리
result_summary = {
    'philosophy_sentences_1915': len(philosophy_sentences),
    'core_context_1915': len(core_context_1915),
    'core_context_1924_no_phil': len(core_context_1924),
    'top_predicates_with_philosophy': predicate_counter.most_common(20),
    'substitute_in_core_context': core_words_1924.most_common(20)
}

import json
with open('data/analysis/philosophy_predicate_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(result_summary, f, ensure_ascii=False, indent=2)

# CSV 저장
pd.DataFrame(core_words_1924.most_common(30), columns=['word', 'count']).to_csv(
    'data/analysis/core_context_substitute_words.csv', index=False, encoding='utf-8-sig'
)

print("저장 완료:")
print("  - data/analysis/philosophy_predicate_analysis.json")
print("  - data/analysis/core_context_substitute_words.csv")
