# -*- coding: utf-8 -*-
"""
135개 참조쌍 최종 검증 - 유효/제외 확정
"""
import pandas as pd
import numpy as np
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 데이터 로드
df = pd.read_csv('data/analysis/paragraph_similarity_top500.csv')
df = df[df['similarity'] >= 0.1].copy()

print('【135개 참조쌍 최종 검증】')
print('=' * 80)

# 제외 목록 (확정)
EXCLUDE_RANKS = {
    # 서수만 공유 (NOISE_ORDINAL)
    7, 8, 28, 29, 90, 100, 114,
    # 범용어만 공유 (NOISE_GENERIC) - 사용자 확정
    17,   # C05-P19 × C03-S04-I05-P14: 공통 0개
    41,   # C14-S02-P04 × C06-S06-P18: 區別, 差異點 (일반 비교 표현)
    52,   # C14-S02-P04 × C06-S06-P21: 區別, 第三
    59,   # C02-P47 × C03-S04-I02-P01: 공통 0개
    60,   # C05-P19 × C03-S04-I06-P08: 宇宙 (단일)
    69,   # C13-S02-P03 × C06-S06-P02: 공통 0개
    71,   # C14-S04-P03 × C06-S06-P18: 差異點, 如何
    72,   # C14-S05-P01 × C03-S03-I02-P11: 道德 (단일, 문맥 상이) - 사용자 확정
    75,   # C08-P05 × C03-S04-I07-P06: 공통 0개
    86,   # C02-P15 × C03-S04-I05-P02: 觀念 (단일)
    87,   # C05-P28 × C03-S04-I06-P08: 宇宙 (단일)
    121,  # C05-P19 × C03-S04-I02-P01: 宇宙 (단일)
    125,  # C07-P03 × C01-S01-I01-P05: 何人, 何故 (의문사)
    126,  # C13-S01-P03 × C03-S04-I05-P14: 世界 (단일)
    129,  # C13-S02-P03 × C06-S06-P06: 공통 0개
    134,  # C21-P04 × C06-S06-P09: 공통 0개
    135,  # C21-P07 × C06-S02-P02: 對照, 如何 (일반 표현)
}

# 포함 목록 (사용자 확정 - 종교학 용어 등)
INCLUDE_RANKS = {
    6,    # C21-P16 × C01-S02-I03-P01: 希望, 超人的, 信仰, 勢力 (종교학 핵심 용어)
    55,   # C21-P15 × C01-S02-I03-P01: 超人的, 勢力 (종교학 용어)
    113,  # C21-P08 × C01-S02-I03-P01: 超人的, 一神敎 (종교학 용어)
    45,   # C21-P16 × C06-S06-P03: 超人的, 勢力, 宗敎 (종교학 용어)
    26,   # C08-P13 × C03-S04-I07-P08: 人類, 不調和 (메치니코프 진화론)
}

# 유효/제외 판정
df['verdict'] = df['rank'].apply(lambda r: 'EXCLUDE' if r in EXCLUDE_RANKS else 'VALID')

# 통계
valid_df = df[df['verdict'] == 'VALID']
exclude_df = df[df['verdict'] == 'EXCLUDE']

print(f'총 검토 대상: {len(df)}개')
print(f'유효 참조쌍: {len(valid_df)}개')
print(f'제외 (노이즈): {len(exclude_df)}개')
print()

# 제외 목록 상세
print('【제외 목록 (24개)】')
print('-' * 80)
for _, row in exclude_df.iterrows():
    print(f"Rank {row['rank']}: {row['pid_1915']} × {row['pid_1924']} ({row['similarity']:.4f})")

# 장별 유효 참조쌍 분포
print('\n' + '=' * 80)
print('【유효 참조쌍 - 1924 장별 분포】')
print('-' * 60)

valid_df['chapter_1924'] = valid_df['pid_1924'].apply(lambda x: re.match(r'(C\d+)', str(x)).group(1) if re.match(r'(C\d+)', str(x)) else None)
ch_counts = valid_df.groupby('chapter_1924').size().sort_index()
for ch, cnt in ch_counts.items():
    print(f'  {ch}: {cnt}개')

print(f'\n  합계: {len(valid_df)}개')

# 1915 장별 분포
print('\n【유효 참조쌍 - 1915 장별 분포】')
print('-' * 60)
valid_df['chapter_1915'] = valid_df['pid_1915'].apply(lambda x: re.match(r'(C\d+)', str(x)).group(1) if re.match(r'(C\d+)', str(x)) else None)
ch_counts_1915 = valid_df.groupby('chapter_1915').size().sort_values(ascending=False)
for ch, cnt in ch_counts_1915.head(10).items():
    print(f'  {ch}: {cnt}개')

# CSV 저장
valid_df.to_csv('data/analysis/validated_pairs_final.csv', index=False, encoding='utf-8-sig')
print(f'\n저장 완료: data/analysis/validated_pairs_final.csv')

# 요약 저장
summary = {
    '총 검토 대상': len(df),
    '유효 참조쌍': len(valid_df),
    '제외 (노이즈)': len(exclude_df),
    '제외 - 서수': 7,
    '제외 - 범용어': len(exclude_df) - 7,
}

print('\n' + '=' * 80)
print('【최종 요약】')
print('-' * 60)
for k, v in summary.items():
    print(f'  {k}: {v}개')
