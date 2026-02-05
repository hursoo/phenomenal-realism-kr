# -*- coding: utf-8 -*-
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_excel('app/data/BK_YD_1924_IY_v1.2.xlsx')
chapters = df[df['line_class'] == 'STRUCT'][['local_id', 'kr_text']]

print("【인내천요의 장 제목】")
for i in range(1, 7):
    cid = f'C0{i}'
    row = chapters[chapters['local_id'] == cid]
    if len(row) > 0:
        print(f"{cid}: {row.iloc[0]['kr_text']}")
