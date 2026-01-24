"""
'哲學' 대체어 추가 사례 발굴:
- 참조쌍에서 1915 '哲學' 포함 문단의 상세 분석
- 1924 대응 문단에서 대체어 패턴 추출
"""

import pandas as pd
import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 데이터 로드
df_1915 = pd.read_excel('app/data/BK_IT_1915_PR_v1.3.xlsx')
df_1924 = pd.read_excel('app/data/BK_YD_1924_IY_v1.2.xlsx')
validated_pairs = pd.read_csv('data/analysis/validated_pairs_final.csv')

print(f"=== 유효 참조쌍: {len(validated_pairs)}개 ===\n")

# ============================================================
# 1단계: 1915 원문에서 '哲學' 포함 문단 전체 추출
# ============================================================
print("=== 1단계: 1915 '哲學' 포함 문단 식별 ===\n")

# 문단 ID 추출 함수
def get_paragraph_id(local_id):
    """local_id에서 문단 ID 추출 (P## 까지)"""
    if pd.isna(local_id):
        return None
    match = re.match(r'(C\d+-(?:S\d+-)?P\d+)', str(local_id))
    if match:
        return match.group(1)
    return None

# 1915에서 '哲學' 포함 문단 찾기
df_1915['para_id'] = df_1915['local_id'].apply(get_paragraph_id)
phil_rows_1915 = df_1915[df_1915['kr_text'].str.contains('哲學', na=False)]
phil_paras_1915 = phil_rows_1915['para_id'].dropna().unique()
print(f"1915 '哲學' 포함 문단 수: {len(phil_paras_1915)}개")

# ============================================================
# 2단계: 참조쌍 중 1915에 '哲學' 포함된 쌍 상세 분석
# ============================================================
print("\n=== 2단계: 참조쌍 내 '哲學' 상세 분석 ===\n")

# 각 참조쌍에서 1915 text에 '哲學'이 포함된 경우 분석
philosophy_cases = []

for idx, row in validated_pairs.iterrows():
    text_1915 = str(row['text_1915']) if pd.notna(row['text_1915']) else ""
    text_1924 = str(row['text_1924']) if pd.notna(row['text_1924']) else ""

    # '哲學' 관련 단어 추출
    phil_words_1915 = re.findall(r'[一-龥]*哲學[一-龥]*', text_1915)
    phil_words_1924 = re.findall(r'[一-龥]*哲學[一-龥]*', text_1924)

    if phil_words_1915:  # 1915에 '哲學' 있는 경우
        philosophy_cases.append({
            'rank': row['rank'],
            'similarity': row['similarity'],
            'pid_1915': row['pid_1915'],
            'pid_1924': row['pid_1924'],
            'chapter_1915': row['chapter_1915'],
            'section_1924': row['section_1924'],
            'phil_1915': phil_words_1915,
            'phil_1924': phil_words_1924,
            'text_1915': text_1915,
            'text_1924': text_1924,
            'has_phil_1924': len(phil_words_1924) > 0
        })

print(f"참조쌍 중 1915에 '哲學' 포함: {len(philosophy_cases)}개")
print(f"  - 1924에도 '哲學' 유지: {sum(1 for c in philosophy_cases if c['has_phil_1924'])}개")
print(f"  - 1924에서 '哲學' 소거: {sum(1 for c in philosophy_cases if not c['has_phil_1924'])}개")

# ============================================================
# 3단계: '哲學' 소거 사례 상세 분석
# ============================================================
print("\n=== 3단계: '哲學' 소거 사례 상세 분석 ===\n")

erased_cases = [c for c in philosophy_cases if not c['has_phil_1924']]

for i, case in enumerate(erased_cases, 1):
    print(f"--- 사례 {i} (rank {case['rank']}, 유사도 {case['similarity']:.3f}) ---")
    print(f"1915: {case['pid_1915']} ({case['chapter_1915']})")
    print(f"  '哲學' 용례: {case['phil_1915']}")
    print(f"  원문: {case['text_1915'][:150]}...")
    print(f"1924: {case['pid_1924']} ({case['section_1924']})")
    print(f"  원문: {case['text_1924'][:150]}...")

    # 1924 텍스트에서 핵심 한자어 추출
    hanja_1924 = re.findall(r'[一-龥]{2,}', case['text_1924'])
    from collections import Counter
    top_hanja = Counter(hanja_1924).most_common(10)
    print(f"  1924 주요 한자어: {top_hanja}")
    print()

# ============================================================
# 4단계: 동일 주제의 문장 구조 비교
# ============================================================
print("\n=== 4단계: 주제별 대체 패턴 분석 ===\n")

# 사례별 대체 패턴 정리
substitution_patterns = []

for case in erased_cases:
    phil_term = case['phil_1915'][0] if case['phil_1915'] else ""

    # 1924에서 주어 위치 단어 추출 (문장 시작 또는 조사 앞)
    # 예: "네로부터 哲人들이" → '哲人'
    potential_subjects = re.findall(r'([一-龥]{2,})[들이가은는을]', case['text_1924'])

    # 핵심 개념어 추출
    key_concepts_1924 = []
    for concept in ['眞理', '原理', '人乃天', '哲人', '道理', '實在', '天道']:
        if concept in case['text_1924']:
            key_concepts_1924.append(concept)

    substitution_patterns.append({
        'rank': case['rank'],
        'phil_1915': phil_term,
        'potential_subjects_1924': potential_subjects[:5],
        'key_concepts_1924': key_concepts_1924,
        'text_1915_short': case['text_1915'][:80],
        'text_1924_short': case['text_1924'][:80]
    })

print("대체 패턴 요약:")
print("-" * 70)
for p in substitution_patterns:
    print(f"Rank {p['rank']}: {p['phil_1915']}")
    print(f"  → 주어 후보: {p['potential_subjects_1924']}")
    print(f"  → 핵심 개념: {p['key_concepts_1924']}")
    print()

# ============================================================
# 5단계: 추가 사례 탐색 - 동일 1924 문단에 매핑된 다른 1915 문단
# ============================================================
print("\n=== 5단계: 동일 1924 문단의 다중 참조 분석 ===\n")

# C03-S04-I02-P01에 매핑된 모든 1915 문단
target_1924 = 'C03-S04-I02-P01'
multi_refs = validated_pairs[validated_pairs['pid_1924'] == target_1924]
print(f"'{target_1924}'에 매핑된 1915 문단 ({len(multi_refs)}개):")
for _, row in multi_refs.iterrows():
    text = str(row['text_1915'])[:100] if pd.notna(row['text_1915']) else ""
    has_phil = '哲學' in text
    print(f"  {row['pid_1915']} (sim: {row['similarity']:.3f}) {'[哲學]' if has_phil else ''}")
    print(f"    → {text}...")

# ============================================================
# 6단계: '哲學' 유지 사례도 분석 (대조군)
# ============================================================
print("\n\n=== 6단계: '哲學' 유지 사례 (대조군) ===\n")

maintained_cases = [c for c in philosophy_cases if c['has_phil_1924']]
for i, case in enumerate(maintained_cases, 1):
    print(f"--- 유지 사례 {i} (rank {case['rank']}) ---")
    print(f"1915 '{case['phil_1915']}': {case['text_1915'][:100]}...")
    print(f"1924 '{case['phil_1924']}': {case['text_1924'][:100]}...")
    print()

# ============================================================
# 7단계: 결과 저장
# ============================================================
print("\n=== 7단계: 결과 저장 ===\n")

# 상세 분석 결과 저장
result_df = pd.DataFrame(philosophy_cases)
result_df.to_csv('data/analysis/philosophy_substitution_detailed.csv', index=False, encoding='utf-8-sig')
print("저장 완료: data/analysis/philosophy_substitution_detailed.csv")

# 대체 패턴 요약
pattern_df = pd.DataFrame(substitution_patterns)
pattern_df.to_csv('data/analysis/philosophy_substitution_patterns.csv', index=False, encoding='utf-8-sig')
print("저장 완료: data/analysis/philosophy_substitution_patterns.csv")
