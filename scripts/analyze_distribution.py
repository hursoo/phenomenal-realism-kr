# -*- coding: utf-8 -*-
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_csv('data/analysis/paragraph_similarity_top500.csv')

print('【유사도 분포 분석】')
print('=' * 50)

# 구간별 개수
thresholds = [0.3, 0.25, 0.2, 0.15, 0.1, 0.08, 0.05, 0.04]
for t in thresholds:
    count = len(df[df['similarity'] >= t])
    print(f'  {t:.2f} 이상: {count}개')

print()
print('【상위 500개 내 유사도 범위】')
print(f'  최대: {df["similarity"].max():.4f}')
print(f'  최소: {df["similarity"].min():.4f}')
print(f'  평균: {df["similarity"].mean():.4f}')
print(f'  중앙값: {df["similarity"].median():.4f}')

# 전체 데이터에서 임계값별 비율
print()
print('【전체 228,490쌍 기준 비율】')
total = 228490
for t in [0.1, 0.08, 0.05]:
    count = len(df[df['similarity'] >= t])
    pct = count / total * 100
    print(f'  {t:.2f} 이상: {count}개 (상위 {pct:.4f}%)')
