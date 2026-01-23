# -*- coding: utf-8 -*-
"""
문단 유사도 ≥ 0.1 기준 장-장 평균 히트맵 생성 (v2)
29개 장(1915) × 6개 장(1924)
- 인내천요의 장 제목 수정
- 세로축 레이블 가로쓰기
- 흰색 셀 = 유의미한 참조 쌍 없음 (0개)
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import sys
import re
sys.stdout.reconfigure(encoding='utf-8')

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

print("=" * 60)
print("【문단 유사도 ≥ 0.1 기준 장-장 평균 히트맵 생성 (v2)】")
print("=" * 60)

# 1. 데이터 로드
df_1915 = pd.read_excel('app/data/BK_IT_1915_PR_v1.3.xlsx')
df_1924 = pd.read_excel('app/data/BK_YD_1924_IY_v1.2.xlsx')

# 2. TEXT만 필터링
df_1915 = df_1915[df_1915['line_class'] == 'TEXT'].copy()
df_1924 = df_1924[df_1924['line_class'] == 'TEXT'].copy()

# 3. 문단 ID 추출 함수
def extract_paragraph_id_1915(local_id):
    if pd.isna(local_id):
        return None
    match = re.match(r'(C\d+(?:-S\d+)?-P\d+)', str(local_id))
    if match:
        return match.group(1)
    match = re.match(r'(C\d+-P\d+)', str(local_id))
    if match:
        return match.group(1)
    return None

def extract_paragraph_id_1924(local_id):
    if pd.isna(local_id):
        return None
    match = re.match(r'(C\d+-S\d+(?:-I\d+)?-P\d+)', str(local_id))
    if match:
        return match.group(1)
    return None

def extract_chapter_1915(pid):
    if pd.isna(pid):
        return None
    match = re.match(r'(C\d+)', str(pid))
    return match.group(1) if match else None

def extract_chapter_1924(pid):
    if pd.isna(pid):
        return None
    match = re.match(r'(C\d+)', str(pid))
    return match.group(1) if match else None

# 4. 문단별 텍스트 집계
df_1915['pid'] = df_1915['local_id'].apply(extract_paragraph_id_1915)
df_1924['pid'] = df_1924['local_id'].apply(extract_paragraph_id_1924)

para_1915 = df_1915.groupby('pid')['kr_text'].apply(lambda x: ' '.join(x.dropna())).reset_index()
para_1924 = df_1924.groupby('pid')['kr_text'].apply(lambda x: ' '.join(x.dropna())).reset_index()

para_1915 = para_1915[para_1915['pid'].notna()]
para_1924 = para_1924[para_1924['pid'].notna()]

print(f"1915 문단 수: {len(para_1915)}")
print(f"1924 문단 수: {len(para_1924)}")

# 5. 한자어 토큰화
def extract_hanja(text):
    if pd.isna(text):
        return set()
    return set(re.findall(r'[一-龥]{2,}', str(text)))

# 6. 자카드 유사도
def jaccard_similarity(set1, set2):
    if not set1 or not set2:
        return 0.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0

# 7. 토큰 집합 생성
para_1915['tokens'] = para_1915['kr_text'].apply(extract_hanja)
para_1924['tokens'] = para_1924['kr_text'].apply(extract_hanja)

para_1915['chapter'] = para_1915['pid'].apply(extract_chapter_1915)
para_1924['chapter'] = para_1924['pid'].apply(extract_chapter_1924)

# 8. 유사도 계산 (≥ 0.1만 저장)
print("\n유사도 계산 중...")
THRESHOLD = 0.1
results = []

total = len(para_1915) * len(para_1924)
count = 0

for _, row1 in para_1915.iterrows():
    for _, row2 in para_1924.iterrows():
        sim = jaccard_similarity(row1['tokens'], row2['tokens'])
        if sim >= THRESHOLD:
            results.append({
                'chapter_1915': row1['chapter'],
                'chapter_1924': row2['chapter'],
                'similarity': sim
            })
        count += 1
        if count % 50000 == 0:
            print(f"  진행: {count:,}/{total:,} ({count/total*100:.1f}%)")

print(f"\n유사도 ≥ {THRESHOLD} 쌍: {len(results)}개")

# 9. 장-장 평균 계산
df_results = pd.DataFrame(results)

chapters_1915 = [f'C{i:02d}' for i in range(29)]  # C00-C28
chapters_1924 = [f'C0{i}' for i in range(1, 7)]  # C01-C06

if len(df_results) > 0:
    # 장-장별 평균 (≥ 0.1인 것들만의 평균)
    chapter_avg = df_results.groupby(['chapter_1915', 'chapter_1924'])['similarity'].mean().reset_index()
    chapter_avg.columns = ['chapter_1915', 'chapter_1924', 'avg_similarity']

    # 장-장별 개수도 함께
    chapter_count = df_results.groupby(['chapter_1915', 'chapter_1924']).size().reset_index(name='count')

    chapter_stats = chapter_avg.merge(chapter_count, on=['chapter_1915', 'chapter_1924'])

    print("\n【장-장별 평균 유사도 (≥0.1인 쌍만) 상위 10개】")
    print("-" * 50)
    for _, row in chapter_stats.sort_values('avg_similarity', ascending=False).head(10).iterrows():
        print(f"  {row['chapter_1915']} × {row['chapter_1924']}: 평균 {row['avg_similarity']:.4f} ({int(row['count'])}개)")

    # 10. 피벗 테이블 생성
    pivot_avg = chapter_stats.pivot(index='chapter_1915', columns='chapter_1924', values='avg_similarity')
    pivot_avg = pivot_avg.reindex(index=chapters_1915, columns=chapters_1924, fill_value=np.nan)

    pivot_count = chapter_stats.pivot(index='chapter_1915', columns='chapter_1924', values='count')
    pivot_count = pivot_count.reindex(index=chapters_1915, columns=chapters_1924, fill_value=0)
else:
    pivot_avg = pd.DataFrame(np.nan, index=chapters_1915, columns=chapters_1924)
    pivot_count = pd.DataFrame(0, index=chapters_1915, columns=chapters_1924)

# 11. CSV 저장
pivot_avg.to_csv('data/analysis/chapter_chapter_matrix_avg_above_threshold.csv')
print(f"\n평균 매트릭스 저장: data/analysis/chapter_chapter_matrix_avg_above_threshold.csv")

# 12. 히트맵 생성
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

# 어노테이션용: 평균값과 개수 함께 표시
annot_data = []
for i, idx in enumerate(chapters_1915):
    row_annot = []
    for j, col in enumerate(chapters_1924):
        avg_val = pivot_avg.loc[idx, col]
        cnt_val = pivot_count.loc[idx, col]
        if pd.isna(avg_val) or cnt_val == 0:
            row_annot.append('')  # 빈 셀
        else:
            row_annot.append(f'{avg_val:.2f}\n({int(cnt_val)}개)')
    annot_data.append(row_annot)

annot_df = pd.DataFrame(annot_data, index=chapters_1915, columns=chapters_1924)

# 히트맵
sns.heatmap(
    pivot_avg,
    annot=annot_df,
    fmt='',
    cmap='YlOrRd',
    xticklabels=col_labels,
    yticklabels=chapters_1915,
    cbar_kws={'label': '평균 유사도 (≥0.1인 쌍만)', 'shrink': 0.5},
    ax=ax,
    vmin=0.1,
    vmax=0.25,
    linewidths=0.5,
    linecolor='lightgray',
    mask=mask,
    annot_kws={'fontsize': 8}
)

# 빈 셀(흰색) 표시를 위해 배경색 설정
ax.set_facecolor('white')

ax.set_xlabel('『인내천요의』(1924)', fontsize=14, fontweight='bold')
ax.set_ylabel('『철학과 종교』(1915)', fontsize=14, fontweight='bold')
ax.set_title('문단 유사도 ≥ 0.1 기준 장-장 평균 히트맵\n(흰색 = 유의미한 참조 쌍 없음)', fontsize=16, fontweight='bold', pad=20)

# y축 레이블 가로쓰기
ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=9)
ax.set_xticklabels(ax.get_xticklabels(), rotation=0, fontsize=9, ha='center')

plt.tight_layout()
plt.savefig('images/chapter_heatmap_avg_above_threshold.png', dpi=150, bbox_inches='tight', facecolor='white')
print(f"히트맵 저장: images/chapter_heatmap_avg_above_threshold.png")

plt.close()

print("\n" + "=" * 60)
print("완료!")
print("\n범례:")
print("  - 색상 셀: 유사도 ≥ 0.1인 문단 쌍이 존재하며, 그 평균값 표시")
print("  - 흰색 셀: 유사도 ≥ 0.1인 문단 쌍이 없음 (0개)")
print("  - 괄호 안 숫자: 해당 장-장 조합의 유의미한 쌍 개수")
