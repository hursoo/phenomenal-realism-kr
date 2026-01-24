# -*- coding: utf-8 -*-
"""
C03-S04 및 C06 Excel 파일 업데이트 (검증된 유효 쌍 기준)
"""
import pandas as pd
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 유효 쌍 로드
df_valid = pd.read_csv('data/analysis/validated_pairs_final.csv')
print(f'유효 참조쌍: {len(df_valid)}개')

# 장/절 추출
df_valid['ch_1915'] = df_valid['pid_1915'].apply(lambda x: re.match(r'(C\d+)', str(x)).group(1) if re.match(r'(C\d+)', str(x)) else None)
df_valid['ch_1924'] = df_valid['pid_1924'].apply(lambda x: re.match(r'(C\d+)', str(x)).group(1) if re.match(r'(C\d+)', str(x)) else None)
df_valid['sect_1924'] = df_valid['pid_1924'].apply(lambda x: re.match(r'(C\d+-S\d+)', str(x)).group(1) if re.match(r'(C\d+-S\d+)', str(x)) else None)
df_valid['item_1924'] = df_valid['pid_1924'].apply(lambda x: re.match(r'(C\d+-S\d+-I\d+)', str(x)).group(1) if re.match(r'(C\d+-S\d+-I\d+)', str(x)) else None)

# ========================================
# C03-S04 Excel 업데이트
# ========================================
print('\n【C03-S04 Excel 업데이트】')
print('=' * 60)

c03s04_df = df_valid[df_valid['sect_1924'] == 'C03-S04'].copy()
print(f'C03-S04 유효 쌍: {len(c03s04_df)}개')

# 항별 요약
item_summary = c03s04_df.groupby('item_1924').agg({
    'rank': 'count',
    'similarity': ['mean', 'max']
}).round(4)
item_summary.columns = ['참조쌍 개수', '평균 유사도', '최대 유사도']
item_summary = item_summary.reset_index()
item_summary.columns = ['항', '참조쌍 개수', '평균 유사도', '최대 유사도']

# 1915 장별 분포
ch_1915_counts = c03s04_df['ch_1915'].value_counts().sort_index()

# 상세 쌍 목록
detail_df = c03s04_df[['rank', 'pid_1924', 'pid_1915', 'similarity', 'ch_1915', 'item_1924']].copy()
detail_df.columns = ['순위', '1924 문단ID', '1915 문단ID', '유사도', '1915 장', '1924 항']
detail_df = detail_df.sort_values('순위')

# Excel 저장
with pd.ExcelWriter('app/data/C03-S04_참조분석.xlsx', engine='openpyxl') as writer:
    # 요약 시트
    summary_data = pd.DataFrame({
        '항목': ['총 유효 쌍', '평균 유사도', '최대 유사도', '노이즈 제외'],
        '값': [len(c03s04_df), c03s04_df['similarity'].mean().round(4),
               c03s04_df['similarity'].max().round(4), '24개 (서수 7 + 범용어 17)']
    })
    summary_data.to_excel(writer, sheet_name='요약', index=False)

    # 항별 요약
    item_summary.to_excel(writer, sheet_name='항별 요약', index=False)

    # 1915 장별 분포
    ch_dist = pd.DataFrame({'1915 장': ch_1915_counts.index, '참조쌍 개수': ch_1915_counts.values})
    ch_dist.to_excel(writer, sheet_name='1915 장별', index=False)

    # 상세 목록
    detail_df.to_excel(writer, sheet_name='상세 쌍 목록', index=False)

print('저장: app/data/C03-S04_참조분석.xlsx')

# 항별 출력
print('\n항별 분포:')
for _, row in item_summary.iterrows():
    print(f"  {row['항']}: {row['참조쌍 개수']}개")

# ========================================
# C06 Excel 업데이트
# ========================================
print('\n' + '=' * 60)
print('【C06 Excel 업데이트】')
print('=' * 60)

c06_df = df_valid[df_valid['ch_1924'] == 'C06'].copy()
print(f'C06 유효 쌍: {len(c06_df)}개')

# 섹션 추출
c06_df['sect_1924'] = c06_df['pid_1924'].apply(lambda x: re.match(r'(C\d+-S\d+)', str(x)).group(1) if re.match(r'(C\d+-S\d+)', str(x)) else None)

# 섹션별 요약
sect_summary = c06_df.groupby('sect_1924').agg({
    'rank': 'count',
    'similarity': ['mean', 'max']
}).round(4)
sect_summary.columns = ['참조쌍 개수', '평균 유사도', '최대 유사도']
sect_summary = sect_summary.reset_index()
sect_summary.columns = ['섹션', '참조쌍 개수', '평균 유사도', '최대 유사도']

# 1915 장별 분포
ch_1915_counts_c06 = c06_df['ch_1915'].value_counts().sort_index()

# 상세 쌍 목록
detail_c06 = c06_df[['rank', 'pid_1924', 'pid_1915', 'similarity', 'ch_1915', 'sect_1924']].copy()
detail_c06.columns = ['순위', '1924 문단ID', '1915 문단ID', '유사도', '1915 장', '섹션']
detail_c06 = detail_c06.sort_values('순위')

# Excel 저장
with pd.ExcelWriter('app/data/C06_참조분석.xlsx', engine='openpyxl') as writer:
    # 요약 시트
    summary_c06 = pd.DataFrame({
        '항목': ['총 유효 쌍', '평균 유사도', '최대 유사도', '노이즈 제외'],
        '값': [len(c06_df), c06_df['similarity'].mean().round(4),
               c06_df['similarity'].max().round(4), '24개 (서수 7 + 범용어 17)']
    })
    summary_c06.to_excel(writer, sheet_name='요약', index=False)

    # 섹션별 요약
    sect_summary.to_excel(writer, sheet_name='섹션별 요약', index=False)

    # 1915 장별 분포
    ch_dist_c06 = pd.DataFrame({'1915 장': ch_1915_counts_c06.index, '참조쌍 개수': ch_1915_counts_c06.values})
    ch_dist_c06.to_excel(writer, sheet_name='1915 장별', index=False)

    # 상세 목록
    detail_c06.to_excel(writer, sheet_name='상세 쌍 목록', index=False)

print('저장: app/data/C06_참조분석.xlsx')

# 섹션별 출력
print('\n섹션별 분포:')
for _, row in sect_summary.iterrows():
    print(f"  {row['섹션']}: {row['참조쌍 개수']}개")
