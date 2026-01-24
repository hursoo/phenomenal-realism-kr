"""
직접적 대체 관계 탐색:
참조쌍에서 이노우에가 '哲學'을 사용한 문단과
이돈화의 대응 문단을 비교하여 대체어 확인
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

# 문단 ID로 텍스트 추출 함수
def get_paragraph_text(df, para_id):
    """문단 ID에 해당하는 모든 문장을 결합"""
    # para_id로 시작하는 모든 행 찾기
    mask = df['local_id'].str.startswith(para_id + '-', na=False) | (df['local_id'] == para_id)
    rows = df[mask]
    if rows.empty:
        return ""
    texts = rows['kr_text'].dropna().tolist()
    return ' '.join(texts)

def extract_hanja(text):
    if pd.isna(text):
        return []
    return re.findall(r'[一-龥]{2,}', str(text))

# ============================================================
# 1단계: 1915 문단에 '哲學'이 포함된 참조쌍 찾기
# ============================================================
print("=== 1단계: '哲學' 포함 참조쌍 탐색 ===\n")

pairs_with_philosophy = []

for idx, row in validated_pairs.iterrows():
    para_1915 = row['pid_1915']
    para_1924 = row['pid_1924']
    similarity = row['similarity']
    text_1915 = str(row['text_1915']) if pd.notna(row['text_1915']) else ""
    text_1924 = str(row['text_1924']) if pd.notna(row['text_1924']) else ""

    # '哲學' 포함 여부
    if '哲學' in text_1915:
        has_phil_1924 = '哲學' in text_1924

        pairs_with_philosophy.append({
            'rank': idx + 1,
            'similarity': similarity,
            '1915_para': para_1915,
            '1924_para': para_1924,
            '1915_has_phil': True,
            '1924_has_phil': has_phil_1924,
            '1915_text': text_1915[:200],
            '1924_text': text_1924[:200],
            '1915_tokens': extract_hanja(text_1915),
            '1924_tokens': extract_hanja(text_1924)
        })

print(f"1915에 '哲學' 포함된 참조쌍: {len(pairs_with_philosophy)}개")
print(f"그 중 1924에도 '哲學' 있는 쌍: {sum(1 for p in pairs_with_philosophy if p['1924_has_phil'])}개")
print(f"1924에서 '哲學' 소거된 쌍: {sum(1 for p in pairs_with_philosophy if not p['1924_has_phil'])}개")

# ============================================================
# 2단계: '哲學' 소거된 쌍에서 대체어 분석
# ============================================================
print("\n=== 2단계: '哲學' 소거 쌍 상세 분석 ===\n")

erased_pairs = [p for p in pairs_with_philosophy if not p['1924_has_phil']]

# 1924 문단에서 고빈도 단어 집계
from collections import Counter
substitute_counter = Counter()

for pair in erased_pairs:
    for token in pair['1924_tokens']:
        substitute_counter[token] += 1

print("'哲學' 소거된 쌍의 1924 문단에서 고빈도 단어:")
for word, count in substitute_counter.most_common(20):
    print(f"  {word}: {count}회")

# ============================================================
# 3단계: 구체적 사례 출력
# ============================================================
print("\n=== 3단계: 구체적 대조 사례 ===\n")

# 상위 유사도 순으로 5개 사례 출력
erased_pairs_sorted = sorted(erased_pairs, key=lambda x: x['similarity'], reverse=True)

for i, pair in enumerate(erased_pairs_sorted[:5], 1):
    print(f"--- 사례 {i} (유사도: {pair['similarity']:.4f}) ---")
    print(f"1915 문단: {pair['1915_para']}")
    print(f"  → 哲學 포함: {pair['1915_text'][:150]}...")
    print(f"1924 문단: {pair['1924_para']}")
    print(f"  → 哲學 부재: {pair['1924_text'][:150]}...")

    # 1924 문단의 주요 단어
    top_tokens = Counter(pair['1924_tokens']).most_common(5)
    print(f"  → 1924 주요 단어: {top_tokens}")
    print()

# ============================================================
# 4단계: 공통 토큰 vs 1924 고유 토큰 분석
# ============================================================
print("\n=== 4단계: 공통 토큰과 대체어 후보 ===\n")

for i, pair in enumerate(erased_pairs_sorted[:3], 1):
    tokens_1915 = set(pair['1915_tokens'])
    tokens_1924 = set(pair['1924_tokens'])

    common = tokens_1915 & tokens_1924
    only_1924 = tokens_1924 - tokens_1915

    # 1915에만 있는 것 중 '哲學' 관련
    phil_related = [t for t in tokens_1915 if '哲學' in t]

    print(f"--- 사례 {i} ---")
    print(f"공통 토큰: {common}")
    print(f"1915 '哲學' 관련: {phil_related}")
    print(f"1924에만 있는 토큰: {only_1924}")
    print()

# 결과 저장
result_df = pd.DataFrame(erased_pairs)
result_df.to_csv('data/analysis/philosophy_erased_pairs.csv', index=False, encoding='utf-8-sig')
print("\n저장 완료: data/analysis/philosophy_erased_pairs.csv")
