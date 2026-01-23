# -*- coding: utf-8 -*-
"""
맹장(Mechnikov) 구간 유사도 검증
C08 (1915) × C03-S04 (1924) 구간
"""
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 상위 500개 문단 쌍 데이터 로드
df = pd.read_csv('data/analysis/paragraph_similarity_top500.csv')

print('【C08 × C03-S04 문단 쌍 (맹장/메치니코프 구간)】')
print('=' * 70)

# C08 × C03-S04 필터링
c08_pairs = df[(df['chapter_1915'] == 'C08') & (df['section_1924'].str.startswith('C03-S04'))]
print(f'상위 500개 중 C08 × C03-S04: {len(c08_pairs)}개')

if len(c08_pairs) > 0:
    print()
    for _, row in c08_pairs.iterrows():
        print(f"【{row['rank']:3d}위】 {row['pid_1915']} × {row['pid_1924']}  유사도: {row['similarity']:.4f}")
        print(f"  1915: {row['text_1915'][:70]}...")
        print(f"  1924: {row['text_1924'][:70]}...")
        print()

# 장-절 매트릭스에서 count 확인
print('\n【장-절 매트릭스 (count ≥ 0.1)】')
print('-' * 50)
df_count = pd.read_csv('data/analysis/chapter_section_matrix_count.csv')
df_count = df_count.set_index('chapter_1915')

# C08 행 전체 확인
c08_row = df_count.loc['C08']
nonzero = c08_row[c08_row > 0]
if len(nonzero) > 0:
    print(f"C08 × (유의미한 참조 있는 절):")
    for col, val in nonzero.items():
        print(f"  {col}: {int(val)}개")
else:
    print("C08: 유의미한 참조 쌍 없음 (모두 0개)")

# 장-절 매트릭스에서 max 확인
print('\n【장-절 매트릭스 (max 유사도)】')
print('-' * 50)
df_max = pd.read_csv('data/analysis/chapter_section_matrix_max.csv')
df_max = df_max.set_index('chapter_1915')

c08_max = df_max.loc['C08']
top3 = c08_max.nlargest(3)
print(f"C08의 최대 유사도 상위 3개 절:")
for col, val in top3.items():
    print(f"  {col}: {val:.4f}")
