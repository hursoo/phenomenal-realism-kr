"""
자카드 유사도 0.1 임계값의 직관적 의미 분석:
- 문단 단위 평균 토큰 수
- 0.1 달성에 필요한 공통 토큰 수
- 실제 0.1 근처 참조쌍의 구체적 예시
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

# 한자어 토큰 추출
def extract_hanja(text):
    if pd.isna(text):
        return []
    return re.findall(r'[一-龥]{2,}', str(text))

# 분석 대상 필터링
def filter_text_rows(df):
    mask = (
        df['line_class'].isin(['TEXT', 'STRUCT']) &
        ~df['structure_id'].isin(['TOC', 'ROOT'])
    )
    return df[mask].copy()

df_1915_text = filter_text_rows(df_1915)
df_1924_text = filter_text_rows(df_1924)

# ============================================================
# 1단계: 문단 단위 평균 토큰 수 계산
# ============================================================
print("=" * 70)
print("1. 문단 단위 평균 토큰 수")
print("=" * 70)

def get_paragraph_id(local_id):
    if pd.isna(local_id):
        return None
    match = re.match(r'(C\d+-(?:S\d+-)?(?:I\d+-)?P\d+)', str(local_id))
    if match:
        return match.group(1)
    return None

# 1915 문단별 토큰 수
df_1915_text['para_id'] = df_1915_text['local_id'].apply(get_paragraph_id)
para_tokens_1915 = {}
for para_id, group in df_1915_text.groupby('para_id'):
    if para_id:
        all_text = ' '.join(group['kr_text'].dropna().tolist())
        tokens = set(extract_hanja(all_text))
        para_tokens_1915[para_id] = len(tokens)

# 1924 문단별 토큰 수
df_1924_text['para_id'] = df_1924_text['local_id'].apply(get_paragraph_id)
para_tokens_1924 = {}
for para_id, group in df_1924_text.groupby('para_id'):
    if para_id:
        all_text = ' '.join(group['kr_text'].dropna().tolist())
        tokens = set(extract_hanja(all_text))
        para_tokens_1924[para_id] = len(tokens)

avg_1915 = sum(para_tokens_1915.values()) / len(para_tokens_1915) if para_tokens_1915 else 0
avg_1924 = sum(para_tokens_1924.values()) / len(para_tokens_1924) if para_tokens_1924 else 0

print(f"\n1915 텍스트:")
print(f"  - 문단 수: {len(para_tokens_1915)}개")
print(f"  - 문단당 평균 고유 한자어: {avg_1915:.1f}개")
print(f"  - 최소: {min(para_tokens_1915.values()) if para_tokens_1915 else 0}개")
print(f"  - 최대: {max(para_tokens_1915.values()) if para_tokens_1915 else 0}개")

print(f"\n1924 텍스트:")
print(f"  - 문단 수: {len(para_tokens_1924)}개")
print(f"  - 문단당 평균 고유 한자어: {avg_1924:.1f}개")
print(f"  - 최소: {min(para_tokens_1924.values()) if para_tokens_1924 else 0}개")
print(f"  - 최대: {max(para_tokens_1924.values()) if para_tokens_1924 else 0}개")

# ============================================================
# 2단계: 0.1 달성에 필요한 공통 토큰 수 계산
# ============================================================
print("\n" + "=" * 70)
print("2. 자카드 유사도 0.1 달성 조건")
print("=" * 70)

print("""
자카드 공식: J(A,B) = |A ∩ B| / |A ∪ B|
            = |A ∩ B| / (|A| + |B| - |A ∩ B|)

J = 0.1일 때:
  |A ∩ B| = 0.1 × (|A| + |B| - |A ∩ B|)
  |A ∩ B| = 0.1|A| + 0.1|B| - 0.1|A ∩ B|
  1.1 × |A ∩ B| = 0.1(|A| + |B|)
  |A ∩ B| = (|A| + |B|) / 11
""")

print("문단 크기별 0.1 달성에 필요한 최소 공통 토큰 수:")
print("-" * 50)
print(f"{'문단A 토큰':>10} {'문단B 토큰':>10} {'필요 공통 토큰':>15}")
print("-" * 50)

test_cases = [
    (5, 5), (10, 10), (15, 15), (20, 20),
    (10, 15), (15, 20), (20, 30),
    (int(avg_1915), int(avg_1924))
]

for a, b in test_cases:
    # J = c / (a + b - c) = 0.1
    # c = 0.1(a + b - c)
    # c = 0.1a + 0.1b - 0.1c
    # 1.1c = 0.1(a + b)
    # c = (a + b) / 11
    min_common = (a + b) / 11
    print(f"{a:>10} {b:>10} {min_common:>15.1f}")

# ============================================================
# 3단계: 유사도 0.1 근처 실제 참조쌍 분석
# ============================================================
print("\n" + "=" * 70)
print("3. 유사도 0.1 근처 실제 참조쌍 상세 분석")
print("=" * 70)

# 유사도 0.1~0.15 구간의 쌍 추출
pairs_near_threshold = validated_pairs[
    (validated_pairs['similarity'] >= 0.1) &
    (validated_pairs['similarity'] < 0.15)
].head(10)

print(f"\n유사도 0.10~0.15 구간 상위 10개 쌍 분석:\n")

for idx, row in pairs_near_threshold.iterrows():
    pid_1915 = row['pid_1915']
    pid_1924 = row['pid_1924']
    sim = row['similarity']

    # 텍스트 추출
    text_1915 = str(row['text_1915']) if pd.notna(row['text_1915']) else ""
    text_1924 = str(row['text_1924']) if pd.notna(row['text_1924']) else ""

    # 토큰 추출
    tokens_1915 = set(extract_hanja(text_1915))
    tokens_1924 = set(extract_hanja(text_1924))

    common = tokens_1915 & tokens_1924
    union = tokens_1915 | tokens_1924

    print(f"--- Rank {row['rank']} (유사도: {sim:.4f}) ---")
    print(f"1915 ({pid_1915}): {len(tokens_1915)}개 토큰")
    print(f"1924 ({pid_1924}): {len(tokens_1924)}개 토큰")
    print(f"공통 토큰 ({len(common)}개): {common}")
    print(f"합집합: {len(union)}개")
    print(f"계산 확인: {len(common)}/{len(union)} = {len(common)/len(union):.4f}")
    print()

# ============================================================
# 4단계: 구체적인 직관적 예시 생성
# ============================================================
print("\n" + "=" * 70)
print("4. 직관적 이해를 위한 핵심 예시")
print("=" * 70)

# 유사도 0.1 딱 근처인 쌍 찾기
exact_threshold = validated_pairs[
    (validated_pairs['similarity'] >= 0.099) &
    (validated_pairs['similarity'] <= 0.105)
]

print(f"\n유사도 정확히 0.10 근처인 쌍 ({len(exact_threshold)}개):\n")

for idx, row in exact_threshold.head(3).iterrows():
    text_1915 = str(row['text_1915']) if pd.notna(row['text_1915']) else ""
    text_1924 = str(row['text_1924']) if pd.notna(row['text_1924']) else ""

    tokens_1915 = set(extract_hanja(text_1915))
    tokens_1924 = set(extract_hanja(text_1924))

    common = tokens_1915 & tokens_1924

    print(f"[Rank {row['rank']}] 유사도 = {row['similarity']:.4f}")
    print(f"  1915 문단: {len(tokens_1915)}개 고유 한자어")
    print(f"  1924 문단: {len(tokens_1924)}개 고유 한자어")
    print(f"  공통 토큰 {len(common)}개: {sorted(common)}")
    print()

print("\n" + "=" * 70)
print("5. 결론: 문단 단위 자카드 0.1의 의미")
print("=" * 70)

print(f"""
■ 평균적인 문단 크기
  - 1915 문단: 평균 {avg_1915:.0f}개 고유 한자어
  - 1924 문단: 평균 {avg_1924:.0f}개 고유 한자어

■ 이 크기에서 유사도 0.1 달성 조건
  - 필요 공통 토큰: 최소 {(avg_1915 + avg_1924) / 11:.0f}개
  - 즉, 두 문단이 {(avg_1915 + avg_1924) / 11:.0f}개 이상의 동일한 한자어를
    공유해야 비로소 유사도 0.1에 도달

■ 의미
  - 단순히 '宗敎', '世界' 같은 범용어 1~2개 공유로는 0.1 미달
  - '唯物論', '唯心論', '實在論' 같은 특정 주제의 전문 용어가
    여러 개 겹쳐야 0.1 도달 가능
  - 문장이 아닌 '문단' 단위라서 토큰 수가 많아지므로,
    0.1은 상당히 엄격한 기준
""")
