# -*- coding: utf-8 -*-
"""
'생명의 정의 (Bewegung/運動)' 관련 문단 유사도 확인
"""
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_csv('data/analysis/paragraph_similarity_top500.csv')

print('【C06 (생명에 수반하는 다섯 가지 특징) 관련 문단 쌍】')
print('=' * 60)

# C06 장과 관련된 쌍 찾기
c06_pairs = df[df['chapter_1915'] == 'C06']
print(f'상위 500개 중 C06 포함: {len(c06_pairs)}개')
print()

if len(c06_pairs) > 0:
    print('[C06 관련 상위 문단 쌍]')
    for _, row in c06_pairs.head(20).iterrows():
        print(f"  {row['rank']:3d}. {row['pid_1915']} × {row['pid_1924']}: {row['similarity']:.4f}")
        print(f"       1915: {row['text_1915'][:60]}...")
        print(f"       1924: {row['text_1924'][:60]}...")
        print()

# C06 vs C03-S04 조합 확인
print()
print('【C06 × C03-S04 조합 (발표문 핵심 구간)】')
print('=' * 60)
c06_c03s04 = df[(df['chapter_1915'] == 'C06') & (df['section_1924'] == 'C03-S04')]
print(f'상위 500개 중 C06 × C03-S04: {len(c06_c03s04)}개')

if len(c06_c03s04) > 0:
    print()
    for _, row in c06_c03s04.iterrows():
        print(f"  {row['rank']:3d}. {row['pid_1915']} × {row['pid_1924']}: {row['similarity']:.4f}")
