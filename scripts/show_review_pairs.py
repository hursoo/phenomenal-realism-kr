# -*- coding: utf-8 -*-
"""
판단 요청 쌍들의 실제 문단 내용 대조
"""
import pandas as pd
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 데이터 로드
df_pairs = pd.read_csv('data/analysis/paragraph_similarity_top500.csv')
df_1915 = pd.read_excel('app/data/BK_IT_1915_PR_v1.3.xlsx')
df_1924 = pd.read_excel('app/data/BK_YD_1924_IY_v1.2.xlsx')

def get_text_1915(pid):
    rows = df_1915[df_1915['local_id'].str.startswith(pid, na=False)]
    if len(rows) > 0:
        return ' '.join(rows['kr_text'].dropna().astype(str))
    return ''

def get_text_1924(pid):
    rows = df_1924[df_1924['local_id'].str.startswith(pid, na=False)]
    if len(rows) > 0:
        return ' '.join(rows['kr_text'].dropna().astype(str))
    return ''

def extract_common_tokens(text1, text2):
    t1 = set(re.findall(r'[一-龥]{2,}', str(text1)))
    t2 = set(re.findall(r'[一-龥]{2,}', str(text2)))
    return t1 & t2

# 판단 요청 쌍들
review_cases = [
    # REVIEW
    (6, 'C21-P16', 'C01-S02-I03-P01', '희망, 超人的, 勢力'),
    # SUSPECT - 종교학 용어 포함
    (55, 'C21-P15', 'C01-S02-I03-P01', '超人的, 勢力'),
    (113, 'C21-P08', 'C01-S02-I03-P01', '超人的, 一神敎'),
    # SUSPECT - 기타 애매
    (26, 'C08-P13', 'C03-S04-I07-P08', '人類, 不調和'),
    (72, 'C14-S05-P01', 'C03-S03-I02-P11', '道德'),
    (45, 'C21-P16', 'C06-S06-P03', '?'),
    (41, 'C14-S02-P04', 'C06-S06-P18', '差異點, 區別'),
]

print('【판단 요청 쌍 - 문단 대조】')
print('=' * 80)

for rank, pid_1915, pid_1924, note in review_cases:
    row = df_pairs[df_pairs['rank'] == rank]
    if len(row) == 0:
        continue

    sim = row.iloc[0]['similarity']
    text_1915 = get_text_1915(pid_1915)
    text_1924 = get_text_1924(pid_1924)
    common = extract_common_tokens(text_1915, text_1924)

    print(f'\n{"="*80}')
    print(f'【Rank {rank}】 유사도: {sim:.4f}')
    print(f'  {pid_1915} × {pid_1924}')
    print(f'  공통 토큰: {common}')
    print('=' * 80)

    print(f'\n[1915 텍스트 - {pid_1915}]')
    print('-' * 40)
    print(text_1915[:400] + ('...' if len(text_1915) > 400 else ''))

    print(f'\n[1924 텍스트 - {pid_1924}]')
    print('-' * 40)
    print(text_1924[:400] + ('...' if len(text_1924) > 400 else ''))

    print(f'\n→ 포함 / 제외? (메모: {note})')
    print()
