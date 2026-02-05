import pandas as pd
import sys
import re
sys.stdout.reconfigure(encoding='utf-8')

# 두 DB 로드
df_1915 = pd.read_excel('app/data/BK_IT_1915_PR_v1.3.xlsx')
df_1924 = pd.read_excel('app/data/BK_YD_1924_IY_v1.2.xlsx')

print("=" * 70)
print("【STRUCT 행 내용 확인】")
print("=" * 70)

# 1915 STRUCT 행 샘플
print("\n■ 1915 텍스트 STRUCT 행 샘플")
print("-" * 50)
struct_1915 = df_1915[df_1915['line_class'] == 'STRUCT']
print(f"  STRUCT 행 총 수: {len(struct_1915)}")
print("\n  [샘플 20개]")
for _, row in struct_1915.head(20).iterrows():
    print(f"  [{row['local_id']}] {row['kr_text'][:50] if pd.notna(row['kr_text']) else 'N/A'}...")

# 1924 STRUCT 행 샘플
print("\n\n■ 1924 텍스트 STRUCT 행 샘플")
print("-" * 50)
struct_1924 = df_1924[df_1924['line_class'] == 'STRUCT']
print(f"  STRUCT 행 총 수: {len(struct_1924)}")
print("\n  [샘플 20개]")
for _, row in struct_1924.head(20).iterrows():
    print(f"  [{row['local_id']}] {row['kr_text'][:50] if pd.notna(row['kr_text']) else 'N/A'}...")

print("\n" + "=" * 70)
print("【문단 단위 유사도 비교 계획】")
print("=" * 70)

# 1. 1915 텍스트 구조 분석
print("\n■ 1915 『철학과 종교』 DB 구조")
print("-" * 50)
print(f"  - 전체 행 수: {len(df_1915)}")
print(f"  - 컬럼: {list(df_1915.columns)}")

# local_id 패턴 분석 (C##-P##-S##)
df_1915_text = df_1915[df_1915['line_class'] == 'TEXT']
df_1915_text = df_1915_text[~df_1915_text['structure_id'].isin(['TOC', 'ROOT'])]

# 문단 ID 추출 (C##-P## 또는 C##-S##-P## 형식)
def extract_paragraph_id_1915(local_id):
    if pd.isna(local_id):
        return None
    local_id = str(local_id)
    # 패턴1: C##-P## (예: C06-P03)
    match1 = re.match(r'(C\d+-P\d+)', local_id)
    if match1:
        return match1.group(1)
    # 패턴2: C##-S##-P## (예: C01-S01-P01)
    match2 = re.match(r'(C\d+-S\d+-P\d+)', local_id)
    if match2:
        return match2.group(1)
    return None

df_1915_text['paragraph_id'] = df_1915_text['local_id'].apply(extract_paragraph_id_1915)
paragraphs_1915 = df_1915_text['paragraph_id'].dropna().unique()
print(f"  - 분석 대상 행 수 (TEXT/STRUCT, TOC/ROOT 제외): {len(df_1915_text)}")
print(f"  - 문단 ID 패턴: C##-P## (예: C06-P03)")
print(f"  - 고유 문단 수: {len(paragraphs_1915)}")

# 장별 문단 수
print("\n  [장별 문단 수]")
chapter_para_1915 = {}
for p in paragraphs_1915:
    chapter = p.split('-')[0]
    chapter_para_1915[chapter] = chapter_para_1915.get(chapter, 0) + 1
for ch in sorted(chapter_para_1915.keys()):
    print(f"    {ch}: {chapter_para_1915[ch]}개 문단")

# 누락된 장 확인
all_chapters = set([f"C{str(i).zfill(2)}" for i in range(29)])
found_chapters = set(chapter_para_1915.keys())
missing = all_chapters - found_chapters
if missing:
    print(f"\n  [누락된 장]: {sorted(missing)}")
    # 누락된 장의 local_id 샘플 확인
    for ch in sorted(missing)[:3]:
        sample = df_1915_text[df_1915_text['structure_id'].str.startswith(ch)]['local_id'].head(3).tolist()
        print(f"    {ch} local_id 샘플: {sample}")

# 2. 1924 텍스트 구조 분석
print("\n\n■ 1924 『인내천요의』 DB 구조")
print("-" * 50)
print(f"  - 전체 행 수: {len(df_1924)}")
print(f"  - 컬럼: {list(df_1924.columns)}")

df_1924_text = df_1924[df_1924['line_class'] == 'TEXT']
df_1924_text = df_1924_text[~df_1924_text['structure_id'].isin(['TOC', 'ROOT'])]

# 문단 ID 추출 (C##-S##-I##-P## 형식)
def extract_paragraph_id_1924(local_id):
    if pd.isna(local_id):
        return None
    # C01-S01-P01-S01 또는 C03-S04-I01-P01-S01 형식
    match = re.match(r'(C\d+-S\d+(?:-I\d+)?-P\d+)', str(local_id))
    return match.group(1) if match else None

df_1924_text['paragraph_id'] = df_1924_text['local_id'].apply(extract_paragraph_id_1924)
paragraphs_1924 = df_1924_text['paragraph_id'].dropna().unique()
print(f"  - 분석 대상 행 수 (TEXT/STRUCT, TOC/ROOT 제외): {len(df_1924_text)}")
print(f"  - 문단 ID 패턴: C##-S##-P## 또는 C##-S##-I##-P##")
print(f"  - 고유 문단 수: {len(paragraphs_1924)}")

# 장별 문단 수
print("\n  [장-절별 문단 수]")
section_para_1924 = {}
for p in paragraphs_1924:
    parts = p.split('-')
    if len(parts) >= 2:
        section = f"{parts[0]}-{parts[1]}"
        section_para_1924[section] = section_para_1924.get(section, 0) + 1
for sec in sorted(section_para_1924.keys()):
    print(f"    {sec}: {section_para_1924[sec]}개 문단")

# 3. 비교 매트릭스 크기
print("\n\n■ 문단 단위 비교 매트릭스")
print("-" * 50)
total_comparisons = len(paragraphs_1915) * len(paragraphs_1924)
print(f"  - 1915 문단 수: {len(paragraphs_1915)}")
print(f"  - 1924 문단 수: {len(paragraphs_1924)}")
print(f"  - 총 비교 셀 수: {len(paragraphs_1915)} × {len(paragraphs_1924)} = {total_comparisons:,}개")

# 4. 샘플 문단 ID 출력
print("\n\n■ 문단 ID 샘플")
print("-" * 50)
print("  [1915 문단 ID 샘플 (처음 10개)]")
for p in sorted(paragraphs_1915)[:10]:
    print(f"    {p}")
print("  ...")
print(f"\n  [1924 문단 ID 샘플 (처음 10개)]")
for p in sorted(paragraphs_1924)[:10]:
    print(f"    {p}")
print("  ...")
