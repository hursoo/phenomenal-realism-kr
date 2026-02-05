# -*- coding: utf-8 -*-
"""인내천요의 緖言(서언) 내용 확인"""
import pandas as pd

df = pd.read_excel(r'C:\hp_data\hp2026\1.연구\phenomenal-realism-kr\data\processed\BK_YD_1924_IY_v1.2.xlsx')

# C01 (第一章 緖言) 내용 추출
c01 = df[df['local_id'].str.startswith('C01', na=False)]
text_rows = c01[c01['line_class'] == 'TEXT']

# 파일로 저장
with open('temp_preface.txt', 'w', encoding='utf-8') as f:
    f.write("=" * 60 + "\n")
    f.write("第一章 緖言 - 전체 내용\n")
    f.write("=" * 60 + "\n\n")

    for idx, row in text_rows.iterrows():
        f.write(str(row['kr_text']) + "\n\n")

print("temp_preface.txt에 저장 완료")
