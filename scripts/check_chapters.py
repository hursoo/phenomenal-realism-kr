# -*- coding: utf-8 -*-
"""인내천요의 장 구조 확인"""
import pandas as pd

df = pd.read_excel(r'C:\hp_data\hp2026\1.연구\phenomenal-realism-kr\data\processed\BK_YD_1924_IY_v1.2.xlsx')

# 장 목록
print("=" * 50)
print("인내천요의 장(chapter) 목록:")
print("=" * 50)
chapters = df[df['line_class'] == 'CHAPTER']['kr_text'].tolist()
for i, c in enumerate(chapters):
    print(f"{i+1}. {c}")

# 서문/발문 관련 키워드 검색
print("\n" + "=" * 50)
print("서문/발문 관련 검색:")
print("=" * 50)
keywords = ['序', '서문', '서론', '발문', '緖言', '凡例', '自序', '跋']
for kw in keywords:
    matches = df[df['kr_text'].str.contains(kw, na=False)]
    if len(matches) > 0:
        print(f"[{kw}] {len(matches)}건 발견")
        for idx, row in matches.head(3).iterrows():
            text = row['kr_text'][:60] + "..." if len(str(row['kr_text'])) > 60 else row['kr_text']
            print(f"    - {text}")
