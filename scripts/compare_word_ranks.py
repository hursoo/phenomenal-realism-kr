"""
두 텍스트의 한자어 빈도 순위 비교 분석
- 상대빈도(‰) 기준으로 순위 산출
- '哲學' 관련 용어의 순위 비교
"""

import pandas as pd
import re
from collections import Counter

# 데이터 로드
df_1915 = pd.read_excel('app/data/BK_IT_1915_PR_v1.3.xlsx')
df_1924 = pd.read_excel('app/data/BK_YD_1924_IY_v1.2.xlsx')

# 분석 대상 필터링 (CLAUDE.md 기준)
def filter_text_rows(df):
    """TEXT, STRUCT 행만 포함, RTC_TEXT/ANNOTATION/TOC/ROOT 제외"""
    mask = (
        df['line_class'].isin(['TEXT', 'STRUCT']) &
        ~df['structure_id'].isin(['TOC', 'ROOT'])
    )
    return df[mask]

df_1915_filtered = filter_text_rows(df_1915)
df_1924_filtered = filter_text_rows(df_1924)

# 한자어 추출 (2자 이상)
def extract_hanja(text):
    if pd.isna(text):
        return []
    return re.findall(r'[一-龥]{2,}', str(text))

# 전체 한자어 토큰 추출
tokens_1915 = []
for text in df_1915_filtered['kr_text']:
    tokens_1915.extend(extract_hanja(text))

tokens_1924 = []
for text in df_1924_filtered['kr_text']:
    tokens_1924.extend(extract_hanja(text))

# 빈도 계산
freq_1915 = Counter(tokens_1915)
freq_1924 = Counter(tokens_1924)

# 전체 토큰 수
total_1915 = len(tokens_1915)
total_1924 = len(tokens_1924)

print(f"=== 기초 통계 ===")
print(f"1915 전체 한자어 토큰: {total_1915:,}개")
print(f"1924 전체 한자어 토큰: {total_1924:,}개")
print(f"1915 고유 한자어 종류: {len(freq_1915):,}종")
print(f"1924 고유 한자어 종류: {len(freq_1924):,}종")

# 상대빈도(‰) 계산 및 순위 산출
def create_rank_df(freq_counter, total, name):
    data = []
    for word, count in freq_counter.items():
        rel_freq = (count / total) * 1000  # 천분율
        data.append({
            'word': word,
            'count': count,
            'rel_freq_permille': round(rel_freq, 3),
        })
    df = pd.DataFrame(data)
    df = df.sort_values('rel_freq_permille', ascending=False).reset_index(drop=True)
    df['rank'] = df.index + 1
    df['source'] = name
    return df

rank_1915 = create_rank_df(freq_1915, total_1915, '1915')
rank_1924 = create_rank_df(freq_1924, total_1924, '1924')

# 상위 30개 출력
print(f"\n=== 1915 철학과 종교: 상위 30개 ===")
print(rank_1915[['rank', 'word', 'count', 'rel_freq_permille']].head(30).to_string(index=False))

print(f"\n=== 1924 인내천요의: 상위 30개 ===")
print(rank_1924[['rank', 'word', 'count', 'rel_freq_permille']].head(30).to_string(index=False))

# '哲學' 관련 용어 순위 확인
print(f"\n=== '哲學' 관련 용어 순위 비교 ===")
philosophy_words = ['哲學', '哲學者', '哲學的', '哲學上']

for word in philosophy_words:
    rank_in_1915 = rank_1915[rank_1915['word'] == word]
    rank_in_1924 = rank_1924[rank_1924['word'] == word]

    if not rank_in_1915.empty:
        r1 = rank_in_1915.iloc[0]
        print(f"1915 '{word}': 순위 {r1['rank']}, 빈도 {r1['count']}회, 상대빈도 {r1['rel_freq_permille']}‰")
    else:
        print(f"1915 '{word}': 없음")

    if not rank_in_1924.empty:
        r2 = rank_in_1924.iloc[0]
        print(f"1924 '{word}': 순위 {r2['rank']}, 빈도 {r2['count']}회, 상대빈도 {r2['rel_freq_permille']}‰")
    else:
        print(f"1924 '{word}': 없음")
    print()

# 주요 개념어 비교 (철학, 종교, 생명, 정신, 진화 등)
print(f"\n=== 주요 개념어 순위 비교 ===")
key_words = ['哲學', '宗敎', '生命', '精神', '進化', '道德', '人間', '意識', '眞理', '人乃天']

comparison_data = []
for word in key_words:
    row = {'word': word}

    r1 = rank_1915[rank_1915['word'] == word]
    if not r1.empty:
        row['1915_rank'] = int(r1.iloc[0]['rank'])
        row['1915_count'] = int(r1.iloc[0]['count'])
        row['1915_permille'] = r1.iloc[0]['rel_freq_permille']
    else:
        row['1915_rank'] = '-'
        row['1915_count'] = 0
        row['1915_permille'] = 0

    r2 = rank_1924[rank_1924['word'] == word]
    if not r2.empty:
        row['1924_rank'] = int(r2.iloc[0]['rank'])
        row['1924_count'] = int(r2.iloc[0]['count'])
        row['1924_permille'] = r2.iloc[0]['rel_freq_permille']
    else:
        row['1924_rank'] = '-'
        row['1924_count'] = 0
        row['1924_permille'] = 0

    comparison_data.append(row)

comparison_df = pd.DataFrame(comparison_data)
print(comparison_df.to_string(index=False))

# 결과 저장
rank_1915.to_csv('data/analysis/word_rank_1915.csv', index=False, encoding='utf-8-sig')
rank_1924.to_csv('data/analysis/word_rank_1924.csv', index=False, encoding='utf-8-sig')
comparison_df.to_excel('data/analysis/key_word_rank_comparison.xlsx', index=False)

print(f"\n=== 결과 파일 저장 완료 ===")
print("- data/analysis/word_rank_1915.csv")
print("- data/analysis/word_rank_1924.csv")
print("- data/analysis/key_word_rank_comparison.xlsx")
