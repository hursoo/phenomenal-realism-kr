# -*- coding: utf-8 -*-
"""
유사도 분포 통계량 계산 스크립트
- crosstab_similarity_data.csv: 장/절 단위 유사도 매트릭스
- final_confirmed_correspondences_with_local_id.csv: 문장 단위 유사도
"""
import pandas as pd
import numpy as np

# 1. 장/절 단위 유사도 매트릭스 분석
print("=" * 70)
print("1. 장/절 단위 유사도 분석 (crosstab_similarity_data.csv)")
print("=" * 70)

df_crosstab = pd.read_csv(r'C:\hp_data\hp2026\1.연구\_철학과종교_backup\02-3_분석(PR-IY)\crosstab_similarity_data.csv', index_col=0)

# 매트릭스의 모든 값을 1차원 배열로 변환
all_values = df_crosstab.values.flatten()
all_values = all_values[~np.isnan(all_values)]  # NaN 제거

print(f"총 셀 수: {len(all_values)}")
print(f"평균 (μ): {np.mean(all_values):.4f}")
print(f"표준편차 (σ): {np.std(all_values):.4f}")
print(f"최소값: {np.min(all_values):.4f}")
print(f"최대값: {np.max(all_values):.4f}")
print(f"중앙값: {np.median(all_values):.4f}")
print()

# 백분위수
percentiles = [50, 75, 90, 95, 99, 99.5, 99.9]
print("백분위수:")
for p in percentiles:
    val = np.percentile(all_values, p)
    print(f"  상위 {100-p:.1f}% (P{p}): {val:.4f}")

print()

# μ + 2σ, μ + 3σ 임계값
mu = np.mean(all_values)
sigma = np.std(all_values)
print(f"μ + 2σ = {mu + 2*sigma:.4f}")
print(f"μ + 3σ = {mu + 3*sigma:.4f}")

# 0.5 이상, 0.6 이상 비율
count_05 = np.sum(all_values >= 0.5)
count_06 = np.sum(all_values >= 0.6)
print(f"\n0.5 이상: {count_05}개 ({count_05/len(all_values)*100:.2f}%)")
print(f"0.6 이상: {count_06}개 ({count_06/len(all_values)*100:.2f}%)")


# 2. 문장 단위 유사도 분석
print("\n")
print("=" * 70)
print("2. 문장 단위 유사도 분석 (final_confirmed_correspondences)")
print("=" * 70)

df_sentence = pd.read_csv(r'C:\hp_data\hp2026\1.연구\_철학과종교_backup\02-3_분석(PR-IY)\final_confirmed_correspondences_with_local_id.csv')

# semantic_sim, hanja_sim, combined_score 각각 분석
for col in ['semantic_sim', 'hanja_sim', 'combined_score']:
    if col in df_sentence.columns:
        values = df_sentence[col].dropna().values
        print(f"\n[{col}]")
        print(f"  총 개수: {len(values)}")
        print(f"  평균: {np.mean(values):.4f}")
        print(f"  표준편차: {np.std(values):.4f}")
        print(f"  최소/최대: {np.min(values):.4f} / {np.max(values):.4f}")
        print(f"  중앙값: {np.median(values):.4f}")


# 3. 발표문에서 언급된 0.6306의 위치
print("\n")
print("=" * 70)
print("3. 0.6306의 통계적 위치")
print("=" * 70)

target_value = 0.6306
mu = np.mean(all_values)
sigma = np.std(all_values)

z_score = (target_value - mu) / sigma
percentile_rank = (np.sum(all_values < target_value) / len(all_values)) * 100

print(f"대상 값: {target_value}")
print(f"Z-score: {z_score:.2f} (평균에서 {z_score:.2f} 표준편차 떨어짐)")
print(f"백분위 순위: 상위 {100 - percentile_rank:.2f}%")
