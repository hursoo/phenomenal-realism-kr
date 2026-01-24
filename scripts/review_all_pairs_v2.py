# -*- coding: utf-8 -*-
"""
135개 참조쌍 전체 재검토 - 우연적/일반적 어휘 공유 식별
"""
import pandas as pd
import numpy as np
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 기존 노이즈 토큰 (서수)
ORDINAL_NOISE = {'第一', '第二', '第三', '第四', '第五', '第六', '第七', '第八', '第九', '第十',
                 '其一', '其二', '其三', '其四', '其五'}

# 일반적/범용 어휘 (우연적 일치 가능성 높음)
GENERIC_TOKENS = {
    # 지시/접속
    '如此', '如何', '所以', '然則', '故로', '卽是', '對照', '比較',
    # 시간/공간
    '現在', '過去', '未來', '今日', '世界', '宇宙',
    # 일반 술어
    '存在', '發展', '進化', '變化', '關係', '區別', '差異',
    # 일반 명사
    '思想', '問題', '意味', '目的', '方法', '程度', '範圍',
}

# 의미있는 전문 용어 (차용 가능성 높음)
MEANINGFUL_TERMS = {
    # 철학 용어
    '唯物論', '唯心論', '實在論', '汎神論', '現象', '本體',
    '唯物', '唯心', '實在', '物質', '精神',
    # 생명/의식 용어
    '生命', '意識', '細胞', '原子', '神經', '動物', '植物',
    # 종교 용어
    '基督敎', '佛敎', '儒敎', '天道敎', '宗敎', '信仰',
    '涅槃', '天國', '復活', '創造', '救濟',
    '神人敎', '神政敎', '德敎', '兼愛', '差別愛',
    # 인내천 관련
    '人乃天', '한울', '天道', '神性', '人性',
}

# 데이터 로드
df = pd.read_csv('data/analysis/paragraph_similarity_top500.csv')
df = df[df['similarity'] >= 0.1].copy()

print('【135개 참조쌍 전체 재검토】')
print('=' * 80)
print(f'총 검토 대상: {len(df)}개')
print()

# 각 쌍에 대해 분석
results = []

for _, row in df.iterrows():
    pid_1915 = row['pid_1915']
    pid_1924 = row['pid_1924']
    sim = row['similarity']

    # 텍스트에서 공통 토큰 추출
    text_1915 = str(row['text_1915']) if pd.notna(row['text_1915']) else ''
    text_1924 = str(row['text_1924']) if pd.notna(row['text_1924']) else ''

    tokens_1915 = set(re.findall(r'[一-龥]{2,}', text_1915))
    tokens_1924 = set(re.findall(r'[一-龥]{2,}', text_1924))
    common = tokens_1915 & tokens_1924

    # 분류
    ordinal_only = common.issubset(ORDINAL_NOISE)

    meaningful = common & MEANINGFUL_TERMS
    generic = common & GENERIC_TOKENS
    other = common - ORDINAL_NOISE - GENERIC_TOKENS - MEANINGFUL_TERMS

    # 판정
    if ordinal_only and len(common) > 0:
        verdict = 'NOISE_ORDINAL'
        reason = f'서수만: {common}'
    elif len(meaningful) == 0 and len(common) <= 2:
        verdict = 'SUSPECT_GENERIC'
        reason = f'의미토큰 없음, 공통 {len(common)}개: {common}'
    elif len(meaningful) == 0 and len(generic) > 0 and len(other) <= 1:
        verdict = 'SUSPECT_GENERIC'
        reason = f'범용어만: {common}'
    elif len(meaningful) > 0:
        verdict = 'MEANINGFUL'
        reason = f'의미토큰: {meaningful}'
    else:
        verdict = 'REVIEW'
        reason = f'검토필요: {common}'

    results.append({
        'rank': row['rank'],
        'pid_1915': pid_1915,
        'pid_1924': pid_1924,
        'similarity': sim,
        'common_count': len(common),
        'meaningful_count': len(meaningful),
        'generic_count': len(generic),
        'verdict': verdict,
        'reason': reason,
        'common_tokens': common,
        'meaningful_tokens': meaningful
    })

df_results = pd.DataFrame(results)

# 통계
print('【판정 결과 통계】')
print('-' * 60)
verdict_counts = df_results['verdict'].value_counts()
for v, c in verdict_counts.items():
    print(f'  {v}: {c}개')

# 노이즈 (서수)
print('\n' + '=' * 80)
print('【NOISE_ORDINAL - 서수만 공유 (기존 노이즈)】')
print('-' * 80)
noise_ordinal = df_results[df_results['verdict'] == 'NOISE_ORDINAL']
for _, row in noise_ordinal.iterrows():
    print(f"Rank {row['rank']}: {row['pid_1915']} × {row['pid_1924']} ({row['similarity']:.4f})")
    print(f"  → {row['reason']}")

# 의심 (범용어)
print('\n' + '=' * 80)
print('【SUSPECT_GENERIC - 범용어/일반어만 공유 (우연적 가능성)】')
print('-' * 80)
suspect = df_results[df_results['verdict'] == 'SUSPECT_GENERIC']
for _, row in suspect.iterrows():
    print(f"Rank {row['rank']}: {row['pid_1915']} × {row['pid_1924']} ({row['similarity']:.4f})")
    print(f"  → {row['reason']}")

# 검토 필요
print('\n' + '=' * 80)
print('【REVIEW - 추가 검토 필요】')
print('-' * 80)
review = df_results[df_results['verdict'] == 'REVIEW']
for _, row in review.iterrows():
    print(f"Rank {row['rank']}: {row['pid_1915']} × {row['pid_1924']} ({row['similarity']:.4f})")
    print(f"  → {row['reason']}")

# 요약
print('\n' + '=' * 80)
print('【요약】')
print('-' * 60)
meaningful_count = len(df_results[df_results['verdict'] == 'MEANINGFUL'])
noise_count = len(noise_ordinal)
suspect_count = len(suspect)
review_count = len(review)

print(f'의미있는 참조 (MEANINGFUL): {meaningful_count}개')
print(f'노이즈 - 서수 (NOISE_ORDINAL): {noise_count}개')
print(f'의심 - 범용어 (SUSPECT_GENERIC): {suspect_count}개')
print(f'추가 검토 필요 (REVIEW): {review_count}개')
print()
print(f'잠정 유효 참조쌍: {meaningful_count}개')
print(f'제외 후보: {noise_count + suspect_count}개')
