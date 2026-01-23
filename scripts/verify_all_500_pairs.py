# -*- coding: utf-8 -*-
"""
상위 500개 문단 쌍 전체 토큰 검증
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

# 노이즈로 판정할 토큰 목록
NOISE_TOKENS = {'第一', '第二', '第三', '第四', '第五', '第六', '第七', '第八', '第九', '第十',
                '其一', '其二', '其三', '其四', '其五',
                '如此', '如何', '所以', '然則', '故로', '卽是'}

# 유사도 >= 0.1인 쌍만
df_above = df[df['similarity'] >= 0.1].copy()

print(f'【상위 500개 중 유사도 ≥ 0.1: {len(df_above)}개 전체 검증】')
print('=' * 80)

noise_only_pairs = []
meaningful_pairs = []
all_meaningful_tokens = Counter()
all_noise_tokens = Counter()

for _, row in df_above.iterrows():
    tokens_1915 = get_hanja_tokens(row['text_1915'])
    tokens_1924 = get_hanja_tokens(row['text_1924'])
    common = tokens_1915 & tokens_1924

    noise = common & NOISE_TOKENS
    meaningful = common - NOISE_TOKENS

    all_meaningful_tokens.update(meaningful)
    all_noise_tokens.update(noise)

    if len(meaningful) == 0 and len(common) > 0:
        noise_only_pairs.append({
            'rank': row['rank'],
            'similarity': row['similarity'],
            'pid_1915': row['pid_1915'],
            'pid_1924': row['pid_1924'],
            'common': common
        })
    else:
        meaningful_pairs.append(row)

print(f'\n✅ 실질적 참조: {len(meaningful_pairs)}개 ({len(meaningful_pairs)/len(df_above)*100:.1f}%)')
print(f'❌ 노이즈만: {len(noise_only_pairs)}개 ({len(noise_only_pairs)/len(df_above)*100:.1f}%)')

print(f'\n【노이즈 쌍 목록 ({len(noise_only_pairs)}개)】')
print('-' * 80)
for p in noise_only_pairs:
    print(f"  순위 {p['rank']:3d} | {p['similarity']:.4f} | {p['pid_1915']} × {p['pid_1924']} | 공통: {sorted(p['common'])}")

print(f'\n【전체 공통 토큰 빈도 (상위 20개)】')
print('-' * 80)
print('★ 학술용어:')
for token, cnt in all_meaningful_tokens.most_common(20):
    print(f'  {token}: {cnt}회')

print('\n○ 노이즈 토큰:')
for token, cnt in all_noise_tokens.most_common(10):
    print(f'  {token}: {cnt}회')
