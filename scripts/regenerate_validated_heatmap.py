# -*- coding: utf-8 -*-
"""
검증된 111개 유효 쌍 기준 히트맵 및 매트릭스 재생성
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 유효 쌍 로드
df = pd.read_csv('data/analysis/validated_pairs_final.csv')
print(f'유효 참조쌍: {len(df)}개')

# 장 추출
df['ch_1915'] = df['pid_1915'].apply(lambda x: re.match(r'(C\d+)', str(x)).group(1) if re.match(r'(C\d+)', str(x)) else None)
df['ch_1924'] = df['pid_1924'].apply(lambda x: re.match(r'(C\d+)', str(x)).group(1) if re.match(r'(C\d+)', str(x)) else None)

# 1915 장 순서
ch_1915_order = ['C01', 'C02', 'C03', 'C04', 'C05', 'C06', 'C07', 'C08', 'C09', 'C10',
                 'C11', 'C12', 'C13', 'C14', 'C15', 'C16', 'C17', 'C18', 'C19', 'C20',
                 'C21', 'C22', 'C23', 'C24', 'C25', 'C26', 'C27', 'C28']

# 1924 장 순서
ch_1924_order = ['C01', 'C02', 'C03', 'C04', 'C05', 'C06']

# 장-장 매트릭스 (count)
ch_ch_count = df.groupby(['ch_1915', 'ch_1924']).size().unstack(fill_value=0)

# 순서 맞추기
ch_ch_count = ch_ch_count.reindex(index=[c for c in ch_1915_order if c in ch_ch_count.index],
                                   columns=[c for c in ch_1924_order if c in ch_ch_count.columns],
                                   fill_value=0)

# CSV 저장
ch_ch_count.to_csv('data/analysis/validated_chapter_chapter_count.csv')
print('저장: data/analysis/validated_chapter_chapter_count.csv')

# 장-장 매트릭스 (평균 유사도)
ch_ch_avg = df.groupby(['ch_1915', 'ch_1924'])['similarity'].mean().unstack(fill_value=0)
ch_ch_avg = ch_ch_avg.reindex(index=[c for c in ch_1915_order if c in ch_ch_avg.index],
                               columns=[c for c in ch_1924_order if c in ch_ch_avg.columns],
                               fill_value=0)
ch_ch_avg.to_csv('data/analysis/validated_chapter_chapter_avg.csv')
print('저장: data/analysis/validated_chapter_chapter_avg.csv')

# 히트맵 생성
fig, ax = plt.subplots(figsize=(10, 14))

# 데이터 준비
data = ch_ch_count.values
rows = ch_ch_count.index.tolist()
cols = ch_ch_count.columns.tolist()

# 히트맵 그리기
im = ax.imshow(data, cmap='YlOrRd', aspect='auto')

# 축 설정
ax.set_xticks(np.arange(len(cols)))
ax.set_yticks(np.arange(len(rows)))
ax.set_xticklabels(cols)
ax.set_yticklabels(rows)

# 라벨
ax.set_xlabel('인내천요의 (1924) 장', fontsize=12)
ax.set_ylabel('철학과 종교 (1915) 장', fontsize=12)
ax.set_title(f'문단 참조쌍 개수 (유효 {len(df)}개, 노이즈 24개 제외)', fontsize=14)

# 셀에 값 표시
for i in range(len(rows)):
    for j in range(len(cols)):
        value = data[i, j]
        if value > 0:
            text_color = 'white' if value > 15 else 'black'
            ax.text(j, i, str(int(value)), ha='center', va='center',
                   color=text_color, fontsize=9, fontweight='bold')

# 컬러바
cbar = ax.figure.colorbar(im, ax=ax, shrink=0.5)
cbar.ax.set_ylabel('참조쌍 개수', rotation=-90, va='bottom')

plt.tight_layout()
plt.savefig('images/validated_chapter_heatmap.png', dpi=150, bbox_inches='tight')
print('저장: images/validated_chapter_heatmap.png')
plt.close()

# 요약 출력
print('\n【장별 참조쌍 분포 요약】')
print('=' * 60)
for col in cols:
    total = ch_ch_count[col].sum()
    print(f'{col}: {total}개')
print(f'\n합계: {ch_ch_count.values.sum()}개')
