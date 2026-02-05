# -*- coding: utf-8 -*-
"""
C03-S04-I01 (實現思想과 人乃天) 내용 확인
"""
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_excel('app/data/BK_YD_1924_IY_v1.2.xlsx')

# I01 전체 내용
i01 = df[df['local_id'].str.startswith('C03-S04-I01', na=False)]
i01_text = i01[i01['line_class'] == 'TEXT'][['local_id', 'kr_text']]

print('【C03-S04-I01: 實現思想과 人乃天】')
print('=' * 70)
print(f'총 {len(i01_text)}개 문장')
print()

# 전체 텍스트 출력
for _, row in i01_text.iterrows():
    print(f"[{row['local_id']}]")
    print(f"  {row['kr_text']}")
    print()
