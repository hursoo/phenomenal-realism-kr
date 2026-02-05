# -*- coding: utf-8 -*-
"""
C03-S04 각 항별 참조 관계 매핑
어느 항이 철학과 종교의 어느 장에서 차용했는지 시각화
"""
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 고유사도 쌍 로드
df_pairs = pd.read_csv('data/analysis/paragraph_similarity_top500.csv')
df_pairs = df_pairs[df_pairs['similarity'] >= 0.1]

# C03-S04와 관련된 쌍만 필터링
c03s04_pairs = df_pairs[df_pairs['section_1924'].str.startswith('C03-S04', na=False)].copy()

# 항(Item) 추출
c03s04_pairs['item_1924'] = c03s04_pairs['pid_1924'].str.extract(r'(C03-S04-I\d+)')

print('【C03-S04 항별 참조 현황】')
print('=' * 70)
print(f'C03-S04 관련 고유사도 쌍 (≥0.1): {len(c03s04_pairs)}개')
print()

# 항 정보
items = {
    'C03-S04-I01': '實現思想과 人乃天',
    'C03-S04-I02': '實在와 人乃天',
    'C03-S04-I03': '汎神觀과 人乃天',
    'C03-S04-I04': '生命과 人乃天',
    'C03-S04-I05': '意識과 人乃天',
    'C03-S04-I06': '靈魂과 人乃天',
    'C03-S04-I07': '進化와 人乃天',
}

# 항별 참조 현황
print('【항별 참조 쌍 개수 및 출처】')
print('-' * 70)

for item_id, item_name in items.items():
    item_pairs = c03s04_pairs[c03s04_pairs['item_1924'] == item_id]

    if len(item_pairs) == 0:
        print(f"\n▣ {item_id}: {item_name}")
        print(f"  → 참조 쌍: 0개 (독자적 서술)")
    else:
        # 출처(1915 장) 분포
        source_dist = item_pairs['chapter_1915'].value_counts()

        print(f"\n▣ {item_id}: {item_name}")
        print(f"  → 참조 쌍: {len(item_pairs)}개")
        print(f"  → 출처 분포:")
        for ch, cnt in source_dist.items():
            print(f"     {ch}: {cnt}개")

print()
print('=' * 70)
print('【요약: 차용 vs 독자적 서술】')
print('-' * 70)

for item_id, item_name in items.items():
    item_pairs = c03s04_pairs[c03s04_pairs['item_1924'] == item_id]
    if len(item_pairs) == 0:
        status = "독자적 서술"
    else:
        sources = item_pairs['chapter_1915'].unique()
        status = f"차용 ({', '.join(sources)})"
    print(f"  {item_id} ({item_name}): {status}")
