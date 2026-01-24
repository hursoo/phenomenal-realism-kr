"""
C03-S04 구간 상세 분석:
- 7개 항(I01~I07)별 '哲學' 출현 빈도
- 각 항별 참조쌍 개수
- 두 지표의 대비 시각화
"""

import pandas as pd
import re
import sys
import io
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 데이터 로드
df_1924 = pd.read_excel('app/data/BK_YD_1924_IY_v1.2.xlsx')
validated_pairs = pd.read_csv('data/analysis/validated_pairs_final.csv')

# 분석 대상 필터링
def filter_text_rows(df):
    mask = (
        df['line_class'].isin(['TEXT', 'STRUCT']) &
        ~df['structure_id'].isin(['TOC', 'ROOT'])
    )
    return df[mask].copy()

df_1924_text = filter_text_rows(df_1924)

# ============================================================
# 1단계: C03-S04 구간의 7개 항 식별
# ============================================================
print("=== 1단계: C03-S04 구간 항 식별 ===\n")

# C03-S04로 시작하는 행 추출
c03s04_rows = df_1924_text[df_1924_text['local_id'].str.startswith('C03-S04', na=False)]
print(f"C03-S04 전체 행 수: {len(c03s04_rows)}")

# 항(I##) 추출
def extract_item(local_id):
    """local_id에서 항(I##) 추출"""
    match = re.search(r'I(\d+)', str(local_id))
    if match:
        return f"I{match.group(1).zfill(2)}"
    return None

c03s04_rows = c03s04_rows.copy()
c03s04_rows['item'] = c03s04_rows['local_id'].apply(extract_item)

# 항별 통계
items = c03s04_rows['item'].dropna().unique()
items = sorted([i for i in items if i])
print(f"발견된 항: {items}")

# ============================================================
# 2단계: 항별 '哲學' 출현 빈도 계산
# ============================================================
print("\n=== 2단계: 항별 '哲學' 출현 빈도 ===\n")

item_philosophy_count = {}

for item in items:
    item_rows = c03s04_rows[c03s04_rows['item'] == item]
    texts = ' '.join(item_rows['kr_text'].dropna().tolist())

    # '哲學' 포함 단어 찾기
    philosophy_matches = re.findall(r'[一-龥]*哲學[一-龥]*', texts)
    count = len(philosophy_matches)

    item_philosophy_count[item] = {
        'count': count,
        'matches': philosophy_matches,
        'row_count': len(item_rows)
    }

    print(f"{item}: '哲學' {count}회, 행수 {len(item_rows)}")
    if philosophy_matches:
        print(f"     용례: {set(philosophy_matches)}")

# ============================================================
# 3단계: 항별 참조쌍 개수 계산
# ============================================================
print("\n=== 3단계: 항별 참조쌍 개수 ===\n")

# C03-S04 관련 참조쌍 필터링
c03s04_pairs = validated_pairs[validated_pairs['section_1924'] == 'C03-S04']
print(f"C03-S04 관련 참조쌍: {len(c03s04_pairs)}개")

# 항별 참조쌍 개수
item_pair_count = {}

for item in items:
    # 해당 항의 문단 ID 패턴
    pattern = f"C03-S04-{item}"
    item_pairs = c03s04_pairs[c03s04_pairs['pid_1924'].str.contains(pattern, na=False)]
    item_pair_count[item] = len(item_pairs)
    print(f"{item}: 참조쌍 {len(item_pairs)}개")

# ============================================================
# 4단계: 항별 제목 추출
# ============================================================
print("\n=== 4단계: 항별 제목 ===\n")

# STRUCT 행에서 제목 추출
struct_rows = df_1924[
    (df_1924['line_class'] == 'STRUCT') &
    (df_1924['local_id'].str.startswith('C03-S04-I', na=False))
]

item_titles = {}
for _, row in struct_rows.iterrows():
    item = extract_item(row['local_id'])
    if item and pd.notna(row['kr_text']):
        # 첫 번째 제목만 사용
        if item not in item_titles:
            title = str(row['kr_text']).strip()
            # 제목 정리 (너무 길면 축약)
            if len(title) > 30:
                title = title[:30] + "..."
            item_titles[item] = title

for item in items:
    title = item_titles.get(item, "(제목 없음)")
    print(f"{item}: {title}")

# ============================================================
# 5단계: 종합 데이터 정리
# ============================================================
print("\n=== 5단계: 종합 데이터 ===\n")

summary_data = []
for item in items:
    summary_data.append({
        'item': item,
        'title': item_titles.get(item, ""),
        'philosophy_count': item_philosophy_count[item]['count'],
        'pair_count': item_pair_count.get(item, 0),
        'row_count': item_philosophy_count[item]['row_count']
    })

summary_df = pd.DataFrame(summary_data)
print(summary_df.to_string(index=False))

# 총계
total_phil = sum(d['philosophy_count'] for d in summary_data)
total_pairs = sum(d['pair_count'] for d in summary_data)
print(f"\n총계: '哲學' {total_phil}회, 참조쌍 {total_pairs}개")

# ============================================================
# 6단계: 시각화
# ============================================================
print("\n=== 6단계: 시각화 생성 ===\n")

fig, ax1 = plt.subplots(figsize=(12, 6))

# X축 설정
x = range(len(items))
width = 0.35

# 왼쪽 Y축: 참조쌍 개수 (막대)
bars = ax1.bar(list(x),
               [item_pair_count.get(item, 0) for item in items],
               width, label='참조쌍 개수', color='#4A90A4', alpha=0.8)
ax1.set_xlabel('C03-S04 항목', fontsize=12)
ax1.set_ylabel('참조쌍 개수', color='#4A90A4', fontsize=12)
ax1.tick_params(axis='y', labelcolor='#4A90A4')
ax1.set_ylim(0, max(item_pair_count.values()) * 1.2 if item_pair_count else 10)

# 막대 위에 숫자 표시
for bar, item in zip(bars, items):
    height = bar.get_height()
    if height > 0:
        ax1.annotate(f'{int(height)}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=10, color='#4A90A4')

# 오른쪽 Y축: '哲學' 빈도 (선)
ax2 = ax1.twinx()
philosophy_counts = [item_philosophy_count[item]['count'] for item in items]
line = ax2.plot(list(x), philosophy_counts,
                'o-', color='#E07B54', linewidth=2, markersize=8, label="'哲學' 출현")
ax2.set_ylabel("'哲學' 출현 빈도", color='#E07B54', fontsize=12)
ax2.tick_params(axis='y', labelcolor='#E07B54')
ax2.set_ylim(0, max(philosophy_counts) * 1.5 if max(philosophy_counts) > 0 else 5)

# 선 위에 숫자 표시
for i, (item, count) in enumerate(zip(items, philosophy_counts)):
    ax2.annotate(f'{count}',
                xy=(i, count),
                xytext=(0, 8),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=10, color='#E07B54', fontweight='bold')

# X축 레이블
item_labels = []
for item in items:
    title = item_titles.get(item, "")
    # 제목에서 핵심어 추출
    if '實在' in title:
        label = f"{item}\n實在"
    elif '生命' in title:
        label = f"{item}\n生命"
    elif '意識' in title:
        label = f"{item}\n意識"
    elif '靈魂' in title:
        label = f"{item}\n靈魂"
    elif '進化' in title:
        label = f"{item}\n進化"
    elif '現實' in title:
        label = f"{item}\n現實"
    elif '汎神' in title:
        label = f"{item}\n汎神"
    else:
        label = item
    item_labels.append(label)

ax1.set_xticks(x)
ax1.set_xticklabels(item_labels, fontsize=10)

# 범례
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=10)

# 제목
plt.title("C03-S04 항별 참조쌍 개수 vs '哲學' 출현 빈도\n(참조 밀도 최대, '哲學' 빈도 최소의 역설)",
          fontsize=14, fontweight='bold')

plt.tight_layout()

# 저장
output_path = 'images/c03s04_philosophy_paradox.png'
plt.savefig(output_path, dpi=150, bbox_inches='tight')
print(f"시각화 저장: {output_path}")

plt.close()

# ============================================================
# 7단계: 결과 저장
# ============================================================
print("\n=== 7단계: 결과 저장 ===\n")

summary_df.to_csv('data/analysis/c03s04_item_analysis.csv', index=False, encoding='utf-8-sig')
print("저장 완료: data/analysis/c03s04_item_analysis.csv")

# 상세 분석 결과
print("\n=== 분석 요약 ===")
print(f"C03-S04 전체 참조쌍: {total_pairs}개")
print(f"C03-S04 전체 '哲學' 출현: {total_phil}회")

# 참조쌍 최다 항
max_pair_item = max(item_pair_count, key=item_pair_count.get)
print(f"참조쌍 최다 항: {max_pair_item} ({item_pair_count[max_pair_item]}개)")

# 哲學 최다 항
max_phil_item = max(item_philosophy_count, key=lambda x: item_philosophy_count[x]['count'])
print(f"'哲學' 최다 항: {max_phil_item} ({item_philosophy_count[max_phil_item]['count']}회)")
