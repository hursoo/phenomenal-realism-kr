# -*- coding: utf-8 -*-
"""
검증된 111개 유효 쌍 기준 히트맵 (기존 형태 유지)
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

print("=" * 60)
print("【검증된 111개 유효 쌍 기준 히트맵 생성】")
print("=" * 60)

# 유효 쌍 로드
df = pd.read_csv('data/analysis/validated_pairs_final.csv')
print(f'유효 참조쌍: {len(df)}개')

# 장 추출
df['chapter_1915'] = df['pid_1915'].apply(lambda x: re.match(r'(C\d+)', str(x)).group(1) if re.match(r'(C\d+)', str(x)) else None)
df['chapter_1924'] = df['pid_1924'].apply(lambda x: re.match(r'(C\d+)', str(x)).group(1) if re.match(r'(C\d+)', str(x)) else None)

# 장 목록
chapters_1915 = [f'C{i:02d}' for i in range(29)]  # C00-C28
chapters_1924 = [f'C0{i}' for i in range(1, 7)]   # C01-C06

# 장-장별 평균 및 개수
chapter_avg = df.groupby(['chapter_1915', 'chapter_1924'])['similarity'].mean().reset_index()
chapter_avg.columns = ['chapter_1915', 'chapter_1924', 'avg_similarity']

chapter_count = df.groupby(['chapter_1915', 'chapter_1924']).size().reset_index(name='count')

chapter_stats = chapter_avg.merge(chapter_count, on=['chapter_1915', 'chapter_1924'])

print("\n【장-장별 평균 유사도 상위 10개】")
print("-" * 50)
for _, row in chapter_stats.sort_values('count', ascending=False).head(10).iterrows():
    print(f"  {row['chapter_1915']} × {row['chapter_1924']}: 평균 {row['avg_similarity']:.4f} ({int(row['count'])}개)")

# 피벗 테이블 생성
pivot_avg = chapter_stats.pivot(index='chapter_1915', columns='chapter_1924', values='avg_similarity')
pivot_avg = pivot_avg.reindex(index=chapters_1915, columns=chapters_1924, fill_value=np.nan)

pivot_count = chapter_stats.pivot(index='chapter_1915', columns='chapter_1924', values='count')
pivot_count = pivot_count.reindex(index=chapters_1915, columns=chapters_1924, fill_value=0)

# CSV 저장
pivot_avg.to_csv('data/analysis/chapter_chapter_matrix_avg_above_threshold.csv')
print(f"\n평균 매트릭스 저장: data/analysis/chapter_chapter_matrix_avg_above_threshold.csv")

# 히트맵 생성
fig, ax = plt.subplots(figsize=(12, 16))

# 1924 장 라벨 (정확한 제목)
chapter_labels_1924 = {
    'C01': '제1장\n緖言',
    'C02': '제2장\n人乃天과天道',
    'C03': '제3장\n人乃天과眞理',
    'C04': '제4장\n人乃天의目的',
    'C05': '제5장\n人乃天의修煉',
    'C06': '제6장\n인내천의雜感'
}

col_labels = [chapter_labels_1924.get(c, c) for c in chapters_1924]

# 히트맵용 마스크 (NaN인 곳)
mask = pivot_avg.isna()

# 어노테이션용: 개수를 먼저, 괄호 안에 평균 유사도
annot_data = []
for i, idx in enumerate(chapters_1915):
    row_annot = []
    for j, col in enumerate(chapters_1924):
        avg_val = pivot_avg.loc[idx, col]
        cnt_val = pivot_count.loc[idx, col]
        if pd.isna(avg_val) or cnt_val == 0:
            row_annot.append('')  # 빈 셀
        else:
            row_annot.append(f'{int(cnt_val)}개\n({avg_val:.2f})')
    annot_data.append(row_annot)

annot_df = pd.DataFrame(annot_data, index=chapters_1915, columns=chapters_1924)

# 개수 기준 마스크 (0인 곳)
mask_count = pivot_count == 0

# 히트맵 (개수 기준 색상)
sns.heatmap(
    pivot_count,
    annot=annot_df,
    fmt='',
    cmap='YlOrRd',
    xticklabels=col_labels,
    yticklabels=chapters_1915,
    cbar_kws={'label': '참조쌍 개수 (노이즈 24개 제외)', 'shrink': 0.5},
    ax=ax,
    vmin=0,
    vmax=35,
    linewidths=0.5,
    linecolor='lightgray',
    mask=mask_count,
    annot_kws={'fontsize': 8}
)

# 빈 셀(흰색) 표시를 위해 배경색 설정
ax.set_facecolor('white')

ax.set_xlabel('『인내천요의』(1924)', fontsize=14, fontweight='bold')
ax.set_ylabel('『철학과 종교』(1915)', fontsize=14, fontweight='bold')
ax.set_title(f'문단 유사도 ≥ 0.1 기준 장-장 평균 히트맵\n(유효 {len(df)}개, 노이즈 24개 제외, 흰색 = 유의미한 참조 쌍 없음)', fontsize=16, fontweight='bold', pad=20)

# y축 레이블 가로쓰기
ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=9)
ax.set_xticklabels(ax.get_xticklabels(), rotation=0, fontsize=9, ha='center')

plt.tight_layout()
plt.savefig('images/chapter_heatmap_avg_above_threshold.png', dpi=150, bbox_inches='tight', facecolor='white')
print(f"히트맵 저장: images/chapter_heatmap_avg_above_threshold.png")

plt.close()

print("\n" + "=" * 60)
print("완료!")
print(f"\n총 유효 쌍: {len(df)}개")
print("=" * 60)
