# -*- coding: utf-8 -*-
"""
모든 주요 장-장 조합의 토큰 오버랩 검증
노이즈(서수 등) vs 실질적 참조(학술용어) 판별
"""
import pandas as pd
import re
import sys
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_csv('data/analysis/paragraph_similarity_top500.csv')

def get_hanja_tokens(text):
    return set(re.findall(r'[一-龥]{2,}', str(text)))

# 노이즈로 판정할 토큰 목록 (흔한 서수/접속사 등)
NOISE_TOKENS = {'第一', '第二', '第三', '第四', '第五', '第六', '第七', '第八', '第九', '第十',
                '其一', '其二', '其三', '其四', '其五',
                '如此', '如何', '所以', '然則', '故로', '卽是'}

def analyze_pair(chapter_1915, section_1924_prefix, name):
    """특정 장-장 조합의 토큰 분석"""
    pairs = df[(df['chapter_1915'] == chapter_1915) &
               (df['section_1924'].str.startswith(section_1924_prefix))]
    pairs = pairs[pairs['similarity'] >= 0.1]

    if len(pairs) == 0:
        return None

    all_common_tokens = Counter()
    noise_only_count = 0
    meaningful_count = 0

    results = []
    for _, row in pairs.iterrows():
        tokens_1915 = get_hanja_tokens(row['text_1915'])
        tokens_1924 = get_hanja_tokens(row['text_1924'])
        common = tokens_1915 & tokens_1924

        # 노이즈 vs 의미있는 토큰 분류
        noise = common & NOISE_TOKENS
        meaningful = common - NOISE_TOKENS

        all_common_tokens.update(common)

        if len(meaningful) == 0 and len(noise) > 0:
            noise_only_count += 1
        elif len(meaningful) > 0:
            meaningful_count += 1

        results.append({
            'rank': row['rank'],
            'similarity': row['similarity'],
            'common': common,
            'noise': noise,
            'meaningful': meaningful
        })

    return {
        'name': name,
        'total': len(pairs),
        'noise_only': noise_only_count,
        'meaningful': meaningful_count,
        'all_tokens': all_common_tokens,
        'details': results
    }

# 분석할 구간 목록
pairs_to_analyze = [
    ('C06', 'C03', 'C06 × C03 (생명의 정의)'),
    ('C13', 'C06', 'C13 × C06 (기독교와 유교)'),
    ('C14', 'C06', 'C14 × C06 (불교와 기독교)'),
    ('C02', 'C03', 'C02 × C03 (현상즉실재론)'),
    ('C05', 'C03', 'C05 × C03 (생명-우주 존재론)'),
    ('C21', 'C01', 'C21 × C01 (종교의 요소)'),
    ('C07', 'C01', 'C07 × C01 (약한 연결)'),
    ('C01', 'C03', 'C01 × C03 (서수 노이즈)'),  # 비교용
]

print('=' * 80)
print('【모든 장-장 조합 토큰 검증 결과】')
print('=' * 80)
print()

for ch1915, sec1924, name in pairs_to_analyze:
    result = analyze_pair(ch1915, sec1924, name)
    if result is None:
        print(f"▣ {name}: 유사도 ≥ 0.1인 쌍 없음")
        print()
        continue

    # 판정
    if result['meaningful'] == 0:
        verdict = "❌ 노이즈 (분석 제외 권장)"
    elif result['noise_only'] > result['meaningful']:
        verdict = "⚠️ 혼재 (주의 필요)"
    else:
        verdict = "✅ 실질적 참조"

    print(f"▣ {name}")
    print(f"  총 {result['total']}개 | 의미있는 쌍: {result['meaningful']}개 | 노이즈만: {result['noise_only']}개")
    print(f"  판정: {verdict}")

    # 주요 공통 토큰 (빈도순)
    top_tokens = result['all_tokens'].most_common(10)
    meaningful_tokens = [(t, c) for t, c in top_tokens if t not in NOISE_TOKENS]
    noise_tokens = [(t, c) for t, c in top_tokens if t in NOISE_TOKENS]

    if meaningful_tokens:
        print(f"  ★ 학술용어: {meaningful_tokens}")
    if noise_tokens:
        print(f"  ○ 서수/접속사: {noise_tokens}")
    print()

print('=' * 80)
print('【판정 기준】')
print('  - 노이즈 토큰: 第一~第十, 其一~其五, 如此, 如何, 所以, 然則 등')
print('  - 의미있는 쌍: 노이즈 아닌 공통 토큰이 1개 이상 있는 쌍')
print('  - 노이즈만: 공통 토큰이 모두 노이즈인 쌍')
print('=' * 80)
