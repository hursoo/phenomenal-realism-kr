"""
대체어 사례의 원문 전체 추출
"""

import pandas as pd
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

df_1915 = pd.read_excel('app/data/BK_IT_1915_PR_v1.3.xlsx')
df_1924 = pd.read_excel('app/data/BK_YD_1924_IY_v1.2.xlsx')

def get_paragraph_text(df, para_prefix):
    """문단 전체 텍스트 추출"""
    rows = df[df['local_id'].str.startswith(para_prefix, na=False)]
    texts = []
    for _, r in rows.iterrows():
        if pd.notna(r['kr_text']):
            texts.append(str(r['kr_text']))
    return ' '.join(texts)

print("=" * 70)
print("사례 B: '哲學宗敎' → '理想의 境涯'")
print("=" * 70)

print("\n[1915] C14-S04-P05:")
print("-" * 50)
text = get_paragraph_text(df_1915, 'C14-S04-P05')
print(text)

print("\n[1924] C06-S06-P16:")
print("-" * 50)
text = get_paragraph_text(df_1924, 'C06-S06-P16')
print(text)

print("\n\n" + "=" * 70)
print("사례 C: '哲學宗敎' → '沒我敎/主我敎'")
print("=" * 70)

print("\n[1915] C14-S04-P05: (위와 동일)")

print("\n[1924] C06-S06-P14:")
print("-" * 50)
text = get_paragraph_text(df_1924, 'C06-S06-P14')
print(text)

print("\n\n" + "=" * 70)
print("사례 D: '哲學' 유지 사례 (대조군)")
print("=" * 70)

print("\n[1915] C14-S02-P05:")
print("-" * 50)
text = get_paragraph_text(df_1915, 'C14-S02-P05')
print(text)

print("\n[1924] C06-S06-P11:")
print("-" * 50)
text = get_paragraph_text(df_1924, 'C06-S06-P11')
print(text)

# 추가 분석: C02 장에서 '哲學' 포함 다른 문단 확인
print("\n\n" + "=" * 70)
print("추가 분석: C02 장의 다른 '哲學' 포함 문단")
print("=" * 70)

# C02에서 哲學 포함 문단 찾기
c02_rows = df_1915[
    (df_1915['local_id'].str.startswith('C02', na=False)) &
    (df_1915['kr_text'].str.contains('哲學', na=False))
]

print(f"\nC02에서 '哲學' 포함 행 수: {len(c02_rows)}")
for _, row in c02_rows.head(10).iterrows():
    print(f"\n{row['local_id']}:")
    print(f"  {str(row['kr_text'])[:150]}...")
