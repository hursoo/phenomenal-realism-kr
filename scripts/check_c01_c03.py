# -*- coding: utf-8 -*-
"""
C01 × C03 문단 쌍 상세 분석
"""
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_csv('data/analysis/paragraph_similarity_top500.csv')

# C01 × C03 필터링
pairs = df[(df['chapter_1915'] == 'C01') & (df['section_1924'].str.startswith('C03'))]

print('【C01 × C03 문단 쌍 분석】')
print('=' * 80)
print(f'상위 500개 중 C01 × C03: {len(pairs)}개')
print()

# 1915 C01 장 제목 확인
df_1915 = pd.read_excel('app/data/BK_IT_1915_PR_v1.3.xlsx')
c01_title = df_1915[df_1915['local_id'] == 'C01']['kr_text'].values
if len(c01_title) > 0:
    print(f"【1915 C01 제목】: {c01_title[0]}")

# C01 하위 절 확인
c01_sections = df_1915[df_1915['local_id'].str.match(r'^C01-S\d+$', na=False)][['local_id', 'kr_text']]
if len(c01_sections) > 0:
    print("  하위 절:")
    for _, row in c01_sections.iterrows():
        print(f"    {row['local_id']}: {row['kr_text']}")

# 1924 C03 장 제목 및 절 확인
df_1924 = pd.read_excel('app/data/BK_YD_1924_IY_v1.2.xlsx')
c03_title = df_1924[df_1924['local_id'] == 'C03']['kr_text'].values
if len(c03_title) > 0:
    print(f"\n【1924 C03 제목】: {c03_title[0]}")

# C03 하위 절 확인
c03_sections = df_1924[df_1924['local_id'].str.match(r'^C03-S0[1-9]$', na=False)][['local_id', 'kr_text']]
if len(c03_sections) > 0:
    print("  하위 절:")
    for _, row in c03_sections.iterrows():
        print(f"    {row['local_id']}: {row['kr_text']}")

print()
print('=' * 80)

# 유사도 ≥ 0.1 쌍만 출력
pairs_above = pairs[pairs['similarity'] >= 0.1]
print(f"\n유사도 ≥ 0.1인 쌍: {len(pairs_above)}개\n")

# 절별 분포 확인
if len(pairs_above) > 0:
    print("【절별 분포】")
    section_dist = pairs_above['section_1924'].value_counts().sort_index()
    for sec, cnt in section_dist.items():
        print(f"  {sec}: {cnt}개")
    print()

for i, (_, row) in enumerate(pairs_above.iterrows(), 1):
    print(f"【{i}/{len(pairs_above)}】 순위 {row['rank']:3d}위 | 유사도: {row['similarity']:.4f}")
    print(f"  문단: {row['pid_1915']} × {row['pid_1924']}")
    print(f"  [1915] {row['text_1915'][:200]}...")
    print(f"  [1924] {row['text_1924'][:200]}...")
    print()
