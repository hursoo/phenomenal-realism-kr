# -*- coding: utf-8 -*-
"""
기존 발표문 수치 vs 새 분석 결과 비교
"""
import pandas as pd
import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 70)
print("【기존 발표문 수치 vs 새 분석 결과 비교】")
print("=" * 70)

# 1. 기존 crosstab 데이터 (장-절 단위)
print("\n■ 기존 crosstab_similarity_data.csv (장-절 단위 결합 후 계산)")
print("-" * 50)
df_old = pd.read_csv('data/analysis/crosstab_similarity_data.csv')
df_old = df_old.set_index('section_id')

# 주요 구간 확인
print(f"  C06 × C03-S04: {df_old.loc['C06', 'C03-S04']:.4f}")
print(f"  C07 × C03-S04: {df_old.loc['C07', 'C03-S04']:.4f}")

# 전체 통계
old_values = df_old.values.flatten()
old_values = old_values[~pd.isna(old_values)]
print(f"\n  전체 통계:")
print(f"    - 평균 (μ): {old_values.mean():.4f}")
print(f"    - 표준편차 (σ): {old_values.std():.4f}")
print(f"    - 최대: {old_values.max():.4f}")
print(f"    - P99: {pd.Series(old_values).quantile(0.99):.4f}")

# 2. 새 분석 결과
print("\n\n■ 새 분석 결과 (문단 단위 계산 → max/count 집계)")
print("-" * 50)

# 새 max 매트릭스
df_new_max = pd.read_csv('data/analysis/chapter_section_matrix_max.csv')
df_new_max = df_new_max.set_index('chapter_1915')

# 새 count 매트릭스
df_new_count = pd.read_csv('data/analysis/chapter_section_matrix_count.csv')
df_new_count = df_new_count.set_index('chapter_1915')

print(f"  C06 × C03-S04:")
print(f"    - max: {df_new_max.loc['C06', 'C03-S04']:.4f}")
print(f"    - count (≥0.1): {df_new_count.loc['C06', 'C03-S04']}개")

print(f"\n  C07 × C03-S04:")
print(f"    - max: {df_new_max.loc['C07', 'C03-S04']:.4f}")
print(f"    - count (≥0.1): {df_new_count.loc['C07', 'C03-S04']}개")

# 통계
with open('data/analysis/similarity_stats.json', 'r', encoding='utf-8') as f:
    stats = json.load(f)

print(f"\n  문단 쌍 전체 통계:")
print(f"    - 평균 (μ): {stats['statistics']['mean']:.4f}")
print(f"    - 표준편차 (σ): {stats['statistics']['std']:.4f}")
print(f"    - 최대: {stats['statistics']['max']:.4f}")
print(f"    - P99: {stats['percentiles']['P99']:.4f}")

# 3. 발표문 인용 수치
print("\n\n■ 발표문 인용 수치 (검증 필요)")
print("-" * 50)
print("  ┌───────────────────────────────────────────────────────────┐")
print("  │ 항목                          │ 발표문   │ 기존crosstab │")
print("  ├───────────────────────────────────────────────────────────┤")
print(f"  │ 전체 평균 (μ)                 │ 0.079    │ {old_values.mean():.3f}       │")
print(f"  │ 전체 표준편차 (σ)             │ 0.077    │ {old_values.std():.3f}       │")
print(f"  │ 생명 정의 (C06×C03-S04)       │ 0.6306   │ {df_old.loc['C06', 'C03-S04']:.4f}     │")
print(f"  │ 나가이 비평 (C07×C03-S04)     │ 0.349    │ {df_old.loc['C07', 'C03-S04']:.4f}     │")
print("  └───────────────────────────────────────────────────────────┘")

# 4. 세 가지 방식 비교 요약
print("\n\n■ 세 가지 분석 방식 비교")
print("-" * 50)
print("""
┌─────────────────┬────────────────────────────────────────────────────┐
│ 방식            │ 설명                                               │
├─────────────────┼────────────────────────────────────────────────────┤
│ A. 발표문 수치  │ 출처 불명 (기존 crosstab과도 불일치)               │
│                 │ μ=0.079, 최대=0.6306                               │
├─────────────────┼────────────────────────────────────────────────────┤
│ B. 기존 crosstab│ 장-절 단위로 텍스트 결합 → Jaccard 계산            │
│                 │ μ=0.079, 최대=0.6348 (C07×C03-S04)                 │
├─────────────────┼────────────────────────────────────────────────────┤
│ C. 새 분석 (max)│ 문단 단위 Jaccard → 장-절별 최대값 집계            │
│                 │ 최대=0.3077 (C13×C06-S06)                          │
├─────────────────┼────────────────────────────────────────────────────┤
│ D. 새 분석(count)│ 문단 단위 Jaccard → 장-절별 0.1이상 개수          │
│                 │ 최대=33개 (C13×C06-S06), C06×C03-S04=24개          │
└─────────────────┴────────────────────────────────────────────────────┘
""")

# 5. C06 vs C07 비교 (발표문 핵심 논증)
print("\n■ C06 vs C07 비교 (발표문 핵심 논증: '유사도의 절벽')")
print("-" * 50)
print("""
발표문 주장: "C06(생명 정의) 0.6306 → C07(나가이 비평) 0.349로 절반 급락"

실제 데이터:
┌────────────────┬────────────┬────────────┬────────────┐
│ 데이터 소스    │ C06×C03-S04│ C07×C03-S04│ 차이       │
├────────────────┼────────────┼────────────┼────────────┤""")
print(f"│ 발표문 인용    │ 0.6306     │ 0.349      │ -45%       │")
print(f"│ 기존 crosstab  │ {df_old.loc['C06', 'C03-S04']:.4f}     │ {df_old.loc['C07', 'C03-S04']:.4f}     │ +31%       │")
print(f"│ 새 분석 (max)  │ {df_new_max.loc['C06', 'C03-S04']:.4f}     │ {df_new_max.loc['C07', 'C03-S04']:.4f}     │ -72%       │")
print(f"│ 새 분석 (count)│ {df_new_count.loc['C06', 'C03-S04']}개        │ {df_new_count.loc['C07', 'C03-S04']}개         │ -100%      │")
print("└────────────────┴────────────┴────────────┴────────────┘")

print("\n※ 주목: 기존 crosstab에서는 오히려 C07이 C06보다 높음!")
print("  → 발표문의 '0.6306(C06) > 0.349(C07)' 주장과 불일치")

print("\n" + "=" * 70)
