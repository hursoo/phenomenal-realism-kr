# -*- coding: utf-8 -*-
"""
'進化' 용례 맥락 분류 분석
- 두 텍스트에서 '進化' 포함 문장 추출
- 공기어(co-occurrence) 기반 맥락 분류
"""
import pandas as pd
import re

# 맥락 분류 키워드
CONTEXT_KEYWORDS = {
    '생물학적': ['生物', '動物', '植物', '進化論', '種', '遺傳', '自然', '淘汰', '本能', '生存', '競爭', '適者',
                '有機', '無機', '細胞', '生理', '身體', '肉體', '器官', '機能'],
    '사회/국가': ['國家', '民族', '社會', '國民', '文明', '人種', '帝國', '强者', '弱者', '支配', '競爭',
                 '優勝', '劣敗', '强國', '弱國', '侵略', '政治'],
    '도덕/정신': ['道德', '精神', '人格', '修養', '天道', '人乃天', '良心', '理想', '神', '聖', '靈',
                '完成', '向上', '發展', '開闢', '大我', '眞理', '善', '惡'],
}

def classify_context(text):
    """문장의 맥락을 분류"""
    scores = {k: 0 for k in CONTEXT_KEYWORDS.keys()}

    for category, keywords in CONTEXT_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                scores[category] += 1

    # 가장 높은 점수의 카테고리 반환
    max_score = max(scores.values())
    if max_score == 0:
        return '기타/중립'

    # 동점일 경우 우선순위: 도덕/정신 > 사회/국가 > 생물학적
    for cat in ['도덕/정신', '사회/국가', '생물학적']:
        if scores[cat] == max_score:
            return cat

    return '기타/중립'


def analyze_text(df, text_name):
    """텍스트에서 '進化' 용례 분석"""
    text_rows = df[df['line_class'] == 'TEXT'].copy()

    # '進化' 포함 문장 추출
    jinhwa_rows = text_rows[text_rows['kr_text'].str.contains('進化', na=False)]

    print(f"\n{'='*60}")
    print(f"{text_name}")
    print(f"{'='*60}")
    print(f"'進化' 포함 문장 수: {len(jinhwa_rows)}")

    # 맥락 분류
    contexts = jinhwa_rows['kr_text'].apply(classify_context)
    context_counts = contexts.value_counts()

    print(f"\n맥락별 분포:")
    total = len(jinhwa_rows)
    for cat in ['생물학적', '사회/국가', '도덕/정신', '기타/중립']:
        count = context_counts.get(cat, 0)
        pct = count / total * 100 if total > 0 else 0
        print(f"  {cat}: {count}회 ({pct:.1f}%)")

    # 샘플 출력 (인코딩 문제로 생략)
    # print(f"\n[샘플 용례]")
    # for cat in ['생물학적', '도덕/정신']:
    #     samples = jinhwa_rows[contexts == cat]['kr_text'].head(2)
    #     if len(samples) > 0:
    #         print(f"\n  <{cat}>")
    #         for i, s in enumerate(samples, 1):
    #             s_short = s[:80] + "..." if len(s) > 80 else s
    #             print(f"    {i}. {s_short}")

    return context_counts, total


# 데이터 로드
print("데이터 로딩 중...")
df_1915 = pd.read_excel(r'C:\hp_data\hp2026\1.연구\phenomenal-realism-kr\data\processed\BK_IT_1915_PR_v1.3.xlsx')
df_1924 = pd.read_excel(r'C:\hp_data\hp2026\1.연구\phenomenal-realism-kr\data\processed\BK_YD_1924_IY_v1.2.xlsx')

# 분석 실행
counts_1915, total_1915 = analyze_text(df_1915, "이노우에 『철학과 종교』 (1915)")
counts_1924, total_1924 = analyze_text(df_1924, "이돈화 『인내천요의』 (1924)")

# 비교 요약
print(f"\n{'='*60}")
print("비교 요약")
print(f"{'='*60}")
print(f"\n{'카테고리':<12} {'이노우에':<20} {'이돈화':<20}")
print("-" * 52)

for cat in ['생물학적', '사회/국가', '도덕/정신', '기타/중립']:
    c1 = counts_1915.get(cat, 0)
    c2 = counts_1924.get(cat, 0)
    p1 = c1 / total_1915 * 100 if total_1915 > 0 else 0
    p2 = c2 / total_1924 * 100 if total_1924 > 0 else 0
    print(f"{cat:<12} {c1:>3}회 ({p1:>5.1f}%)       {c2:>3}회 ({p2:>5.1f}%)")

print(f"\n총계         {total_1915:>3}회 (100.0%)       {total_1924:>3}회 (100.0%)")
