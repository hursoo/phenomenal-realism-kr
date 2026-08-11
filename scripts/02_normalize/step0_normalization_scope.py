"""상류 정규화 step 0 — 스코핑 진단.

산출:
  1) 코퍼스 漢字 어휘 V (4종) — 토큰 수·소스 분포
  2) 한자음 읽기 역사전 + *동음 충돌* 목록 (읽기 → 漢字 다의)
  3) 1915 자형(新字体) 이슈 — 1915-only 漢字, shinjitai 탐지 + 한국측 정자 존재 여부

자원: hanja(한국 한자음), 표준 shinjitai→정자 표본표.
완벽 아님 — 규모 가늠용.
"""
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import openpyxl
import hanja

sys.stdout.reconfigure(encoding='utf-8')
OUT = Path(__file__).resolve().parent.parent / 'output'

DBS = [
    ('1915', 'BK_IT_1915_PR_v1.4.xlsx'),
    ('1924', 'BK_YD_1924_IY_v1.3.xlsx'),
    ('개벽', 'MA_YD_10-20_GB.xlsx'),
    ('월보', 'MA_YD_10-20_WB.xlsx'),
]
HANJA_TOK = re.compile(r'[一-鿿]{2,}')
HANJA_CHAR = re.compile(r'[一-鿿]')

# 대표 shinjitai(新字体) → 정자(正字) 표본 (철학·종교·일반 빈출)
SHINJITAI = {
    '実':'實','学':'學','仏':'佛','会':'會','数':'數','医':'醫','独':'獨','国':'國',
    '体':'體','帰':'歸','旧':'舊','当':'當','党':'黨','弁':'辯','戦':'戰','続':'續',
    '経':'經','釈':'釋','価':'價','観':'觀','覚':'覺','円':'圓','処':'處','写':'寫',
    '単':'單','厳':'嚴','双':'雙','圧':'壓','囲':'圍','区':'區','県':'縣','広':'廣',
    '万':'萬','来':'來','両':'兩','礼':'禮','歴':'歷','売':'賣','読':'讀','拝':'拜',
    '検':'檢','験':'驗','顕':'顯','蔵':'藏','鉄':'鐵','転':'轉','軽':'輕','辺':'邊',
    '関':'關','静':'靜','駅':'驛','густ':'X','処':'處','悪':'惡','annot':'X',
    '応':'應','図':'圖','団':'團','属':'屬','糸':'絲','総':'總','聴':'聽','虫':'蟲',
    '亜':'亞','逓':'遞','勧':'勸','巻':'卷','叙':'敘','声':'聲','摂':'攝','戸':'戶',
}
SHINJITAI = {k:v for k,v in SHINJITAI.items() if len(k)==1 and '一'<=k<='鿿'}


def read(tok):
    try:
        return hanja.translate(tok, 'substitution')
    except Exception:
        return tok


def load_text(path):
    wb = openpyxl.load_workbook(path, read_only=True); ws = wb.active
    rows = list(ws.iter_rows(values_only=True)); wb.close()
    hdr = list(rows[0])
    tc = next((hdr.index(c) for c in ('raw_text','kr_text','text') if c in hdr), None)
    lc = hdr.index('line_class') if 'line_class' in hdr else None
    out = []
    for r in rows[1:]:
        if lc is not None and r[lc] not in ('TEXT','RTC_TEXT'):
            continue
        if tc is not None and r[tc]:
            out.append(str(r[tc]))
    return '\n'.join(out)


# === 1. V 구축 ===
tok_freq = Counter()
tok_src = defaultdict(set)
char_src = defaultdict(set)
src_texts = {}
for label, fn in DBS:
    txt = load_text(OUT / fn); src_texts[label] = txt
    for t in HANJA_TOK.findall(txt):
        tok_freq[t] += 1; tok_src[t].add(label)
    for c in set(HANJA_CHAR.findall(txt)):
        char_src[c].add(label)

print('=== 1. 코퍼스 漢字 어휘 V ===')
print(f'  고유 漢字 토큰(2자+): {len(tok_freq):,}')
print(f'  고유 漢字 단자(char): {len(char_src):,}')
for label, _ in DBS:
    n = sum(1 for t in tok_src if label in tok_src[t])
    print(f'    {label}: {n:,} 토큰종류')

# === 2. 읽기 역사전 + 동음 충돌 ===
reading_map = defaultdict(list)   # 읽기 → [漢字토큰...]
for t in tok_freq:
    r = read(t)
    if re.search(r'[一-鿿]', r):   # 변환 실패(미커버 한자 잔존)
        continue
    reading_map[r].append(t)

collisions = {r: toks for r, toks in reading_map.items() if len(toks) > 1}
print('\n=== 2. 한자음 읽기 / 동음 충돌 ===')
print(f'  변환 성공 토큰: {sum(len(v) for v in reading_map.values()):,} / {len(tok_freq):,}')
print(f'  고유 읽기 수: {len(reading_map):,}')
print(f'  동음 충돌 읽기(2개 이상 漢字): {len(collisions):,}')
# 충돌 중 코퍼스 빈도 합이 큰 상위 25
coll_sorted = sorted(collisions.items(), key=lambda kv: sum(tok_freq[t] for t in kv[1]), reverse=True)
print('  --- 빈도 상위 25 충돌 (읽기 | 漢字(빈도) ...) ---')
for r, toks in coll_sorted[:25]:
    parts = ' / '.join(f'{t}({tok_freq[t]})' for t in sorted(toks, key=lambda x:-tok_freq[x]))
    print(f'    {r:<8} {parts}')

# === 3. 1915 자형 이슈 ===
print('\n=== 3. 1915 자형(新字体) 점검 ===')
chars_1915 = {c for c, s in char_src.items() if '1915' in s}
chars_kr = {c for c, s in char_src.items() if s & {'1924','개벽','월보'}}
only_1915 = chars_1915 - chars_kr
print(f'  1915 고유 漢字 단자: {len(chars_1915):,}')
print(f'  1915에만 있고 한국측엔 없는 단자: {len(only_1915):,}')
# shinjitai 탐지
sj_found = sorted(c for c in chars_1915 if c in SHINJITAI)
print(f'  1915에서 발견된 新字体(표본표 기준): {len(sj_found)}개 -> {"".join(sj_found)}')
hit = []
for c in sj_found:
    trad = SHINJITAI[c]
    in_kr = trad in chars_kr
    hit.append((c, trad, in_kr))
print('  --- 新字体 c → 정자 trad | 정자가 한국측에 존재? (존재=매칭 누락 발생) ---')
for c, trad, in_kr in hit:
    print(f'    {c} → {trad} | 한국측 정자 존재: {in_kr}')
n_problem = sum(1 for _,_,k in hit if k)
print(f'  => 매칭 누락 유발 추정(新字体이고 한국측에 정자 존재): {n_problem}개')

print('\n=== step 0 끝 ===')
