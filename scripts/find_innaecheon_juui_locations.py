# -*- coding: utf-8 -*-
"""
C03-S04 내 人乃天主義 사용 위치 상세 확인
"""
import pandas as pd
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_excel('app/data/BK_YD_1924_IY_v1.2.xlsx')

# C03-S04만 필터링
c03s04 = df[df['local_id'].str.startswith('C03-S04', na=False)].copy()

# 인내천주의 포함 행 찾기
c03s04['has_term'] = c03s04['kr_text'].apply(lambda x: bool(re.search(r'人乃天主義', str(x))))
matches = c03s04[c03s04['has_term']]

print('【C03-S04 내 人乃天主義 사용 위치】')
print('=' * 70)
print(f'총 {len(matches)}개 행에서 발견')
print()

for _, row in matches.iterrows():
    print(f"[{row['local_id']}]")
    text = str(row['kr_text'])
    # 人乃天主義 부분 강조
    text_highlighted = text.replace('人乃天主義', '【人乃天主義】')
    print(f"  {text_highlighted[:150]}...")
    print()
