# -*- coding: utf-8 -*-
"""
C13 × C06 상세 분석 (I02 수준)
- 1915 C13: 基督敎と儒敎 (기독교와 유교)
- 1924 C06-S06: 世界三大宗教의 差異点과 人乃天 (P02-P08)
"""
import pandas as pd
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 데이터 로드
df_valid = pd.read_csv('data/analysis/validated_pairs_final.csv')
df_1915 = pd.read_excel('app/data/BK_IT_1915_PR_v1.3.xlsx')
df_1924 = pd.read_excel('app/data/BK_YD_1924_IY_v1.2.xlsx')

# C13 × C06 필터링
df_valid['ch_1915'] = df_valid['pid_1915'].apply(lambda x: re.match(r'(C\d+)', str(x)).group(1) if re.match(r'(C\d+)', str(x)) else None)
df_valid['ch_1924'] = df_valid['pid_1924'].apply(lambda x: re.match(r'(C\d+)', str(x)).group(1) if re.match(r'(C\d+)', str(x)) else None)

c13_c06 = df_valid[(df_valid['ch_1915'] == 'C13') & (df_valid['ch_1924'] == 'C06')].copy()
print(f'【C13 × C06 유효 참조쌍: {len(c13_c06)}개】')
print('=' * 80)

# 텍스트 가져오기 함수
def get_text_1915(pid):
    rows = df_1915[df_1915['local_id'].str.startswith(pid, na=False)]
    rows = rows[rows['line_class'] == 'TEXT']
    if len(rows) > 0:
        return ' '.join(rows['kr_text'].dropna().astype(str))
    return ''

def get_text_1924(pid):
    rows = df_1924[df_1924['local_id'].str.startswith(pid, na=False)]
    rows = rows[rows['line_class'] == 'TEXT']
    if len(rows) > 0:
        return ' '.join(rows['kr_text'].dropna().astype(str))
    return ''

def get_struct_1924(pid):
    rows = df_1924[df_1924['local_id'].str.startswith(pid, na=False)]
    rows = rows[rows['line_class'] == 'STRUCT']
    if len(rows) > 0:
        return rows.iloc[0]['kr_text']
    return ''

# 공통 토큰 추출
def extract_common_tokens(text1, text2):
    t1 = set(re.findall(r'[一-龥]{2,}', str(text1)))
    t2 = set(re.findall(r'[一-龥]{2,}', str(text2)))
    return t1 & t2

# 1915 C13 구조
print('\n【1915 C13 구조: 基督敎と儒敎】')
print('-' * 60)
c13_1915 = df_1915[df_1915['local_id'].str.startswith('C13', na=False)]
c13_struct = c13_1915[c13_1915['line_class'] == 'STRUCT']
for _, row in c13_struct.iterrows():
    print(f"{row['local_id']}: {row['kr_text']}")

# 1924 C06-S06 P02-P08 (儒基 비교 구간) 구조
print('\n【1924 C06-S06 구조: 儒敎와 基督敎 비교 (P02-P08)】')
print('-' * 60)

# P02-P08 각 문단 분석
paragraphs_1924 = ['C06-S06-P02', 'C06-S06-P03', 'C06-S06-P04', 'C06-S06-P05',
                   'C06-S06-P06', 'C06-S06-P07', 'C06-S06-P08']

for pid in paragraphs_1924:
    text = get_text_1924(pid)
    # 해당 문단과 연결된 참조쌍 수
    count = len(c13_c06[c13_c06['pid_1924'].str.startswith(pid)])
    print(f'{pid}: {count}개 참조쌍')
    print(f'  → {text[:100]}...' if len(text) > 100 else f'  → {text}')
    print()

# 1924 문단별 상세 분석 (I02 스타일)
print('\n' + '=' * 80)
print('【C06-S06 儒基 비교 구간 (P02-P08) 문단별 상세 분석】')
print('=' * 80)

paragraph_analysis = []
for pid in paragraphs_1924:
    text = get_text_1924(pid)
    pairs = c13_c06[c13_c06['pid_1924'].str.startswith(pid)]
    count = len(pairs)

    # 내용 요약 (첫 50자)
    summary = text[:50] + '...' if len(text) > 50 else text

    # 주요 1915 참조 장
    if count > 0:
        main_sources = pairs['pid_1915'].value_counts().head(3).index.tolist()
        sources_str = ', '.join(main_sources)
        nature = '차용'
    else:
        sources_str = '-'
        nature = '독자적'

    paragraph_analysis.append({
        'pid': pid,
        'summary': summary,
        'count': count,
        'sources': sources_str,
        'nature': nature
    })

    print(f'\n**{pid}** ({nature}, {count}개 참조쌍)')
    print(f'  내용: {summary}')
    if count > 0:
        print(f'  원천: {sources_str}')

# 비교 항목별 대응 분석
print('\n' + '=' * 80)
print('【儒基 비교 항목별 대응 분석】')
print('=' * 80)

# 이돈화의 비교 항목 (甲~己)
comparison_items = {
    'P02': '第一 儒敎와 基督敎의 差異点 (서두)',
    'P03': '甲 信仰 vs 德敎',
    'P04': '乙 創造 vs 發展',
    'P05': '丙 來世 vs 現世',
    'P06': '丁 復活',
    'P07': '戊 性惡 vs 性善',
    'P08': '己 兼愛 vs 差別愛'
}

for pid in paragraphs_1924:
    para_num = pid.split('-')[-1]
    item_name = comparison_items.get(para_num, para_num)
    pairs = c13_c06[c13_c06['pid_1924'].str.startswith(pid)]
    count = len(pairs)

    print(f'\n【{item_name}】 ({count}개 참조쌍)')

    if count > 0:
        # 공통 토큰 분석
        text_1924 = get_text_1924(pid)
        all_common = set()
        for _, row in pairs.iterrows():
            text_1915 = get_text_1915(row['pid_1915'])
            common = extract_common_tokens(text_1915, text_1924)
            all_common.update(common)

        print(f'  공통 핵심 토큰: {all_common}')
        print(f'  1915 원천:')
        for _, row in pairs.iterrows():
            print(f'    - {row["pid_1915"]} (유사도: {row["similarity"]:.4f})')

# 1915 섹션별 참조 분포
print('\n' + '=' * 80)
print('【1915 C13 섹션별 참조쌍 분포】')
print('-' * 60)

c13_c06['sect_1915'] = c13_c06['pid_1915'].apply(lambda x: re.match(r'(C13-S\d+)', str(x)).group(1) if re.match(r'(C13-S\d+)', str(x)) else 'C13')
sect_counts = c13_c06.groupby('sect_1915').size().sort_index()
for sect, cnt in sect_counts.items():
    print(f'  {sect}: {cnt}개')

# 참조쌍 전체 목록
print('\n' + '=' * 80)
print('【참조쌍 상세 목록 (31개)】')
print('=' * 80)

c13_c06_sorted = c13_c06.sort_values('similarity', ascending=False)
for _, row in c13_c06_sorted.iterrows():
    text_1915 = get_text_1915(row['pid_1915'])
    text_1924 = get_text_1924(row['pid_1924'])
    common = extract_common_tokens(text_1915, text_1924)

    print(f"\n[Rank {row['rank']}] {row['pid_1924']} × {row['pid_1915']} (유사도: {row['similarity']:.4f})")
    print(f"  공통: {common}")

# 요약
print('\n' + '=' * 80)
print('【요약】')
print('-' * 60)
print(f'총 유효 참조쌍: {len(c13_c06)}개')
print(f'평균 유사도: {c13_c06["similarity"].mean():.4f}')
print(f'최대 유사도: {c13_c06["similarity"].max():.4f}')
print(f'\n1924 참조 문단 (P02-P08):')
for item in paragraph_analysis:
    print(f'  {item["pid"]}: {item["count"]}개 ({item["nature"]})')
