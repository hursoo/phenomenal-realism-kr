# -*- coding: utf-8 -*-
"""
분석 보고서용 엑셀 데이터 생성
"""
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Load validated pairs
df = pd.read_csv('data/analysis/validated_pairs_final.csv')

# Create summary statistics
stats = {
    '항목': ['총 문단 쌍', '유효 참조쌍', '임계값', '노이즈 제외', '평균 유사도', '최대 유사도', '최소 유사도'],
    '값': [228490, len(df), 0.1, 24, round(df['similarity'].mean(), 4), round(df['similarity'].max(), 4), round(df['similarity'].min(), 4)]
}
summary_df = pd.DataFrame(stats)

# Chapter distribution
chapter_dist = df.groupby(['chapter_1915', 'chapter_1924']).size().reset_index(name='count')
chapter_dist_pivot = chapter_dist.pivot(index='chapter_1915', columns='chapter_1924', values='count').fillna(0).astype(int)

# Top pairs by chapter combination
top_combinations = df.groupby(['chapter_1915', 'chapter_1924']).agg({
    'similarity': ['count', 'mean', 'max']
}).round(4)
top_combinations.columns = ['참조쌍수', '평균유사도', '최대유사도']
top_combinations = top_combinations.sort_values('참조쌍수', ascending=False).head(15).reset_index()

# Section-level analysis for key chapters
c03_pairs = df[df['chapter_1924'] == 'C03'].copy()
c06_pairs = df[df['chapter_1924'] == 'C06'].copy()

# Save to Excel
with pd.ExcelWriter('docs/analysis-reports/paragraph-similarity-data.xlsx', engine='openpyxl') as writer:
    # Sheet 1: Summary
    summary_df.to_excel(writer, sheet_name='요약통계', index=False)

    # Sheet 2: Chapter distribution
    chapter_dist_pivot.to_excel(writer, sheet_name='장별분포')

    # Sheet 3: Top combinations
    top_combinations.to_excel(writer, sheet_name='주요조합', index=False)

    # Sheet 4: C03 pairs
    c03_pairs.to_excel(writer, sheet_name='C03_참조쌍', index=False)

    # Sheet 5: C06 pairs
    c06_pairs.to_excel(writer, sheet_name='C06_참조쌍', index=False)

    # Sheet 6: All valid pairs
    df.to_excel(writer, sheet_name='전체유효참조쌍', index=False)

print('Excel file created: docs/analysis-reports/paragraph-similarity-data.xlsx')
print(f'Total valid pairs: {len(df)}')
print(f'C03 pairs: {len(c03_pairs)}')
print(f'C06 pairs: {len(c06_pairs)}')
print('\nTop 5 chapter combinations:')
print(top_combinations.head())
