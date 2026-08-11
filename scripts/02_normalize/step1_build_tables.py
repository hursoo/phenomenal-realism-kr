"""상류 정규화 step 1 — 이체자 통일표 + 동음이의 shortlist 도출.

방법:
  같은 한자음 읽기로 묶인 토큰들 안에서,
  - *한 글자만 다른* 동길이 단어쌍 → 그 글자쌍을 이체자 후보로 기록.
    여러 단어 맥락에서 반복되는 글자쌍(support>=2)만 신뢰(체계적 이체자),
    1회뿐인 것은 OCR 의심으로 분리.
  - 이체자 통일을 적용한 뒤에도 같은 읽기에 *서로 다른 정자 단어*가
    둘 이상(각 빈도>=T) 남으면 → 진짜 동음이의 shortlist (Soo 검토).

산출:
  output/variant_unification_2026-05-21.csv      (이체자: 희소형->우세형)
  output/variant_lowconf_ocr_2026-05-21.csv       (1회 맥락; OCR 의심)
  output/homophone_shortlist_2026-05-21.csv        (진짜 동음이의)
완벽 아님 — 검토용 후보.
"""
import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import openpyxl
import hanja

sys.stdout.reconfigure(encoding='utf-8')
OUT = Path(__file__).resolve().parent.parent / 'output'
DBS = [('1915','BK_IT_1915_PR_v1.4.xlsx'),('1924','BK_YD_1924_IY_v1.3.xlsx'),
       ('개벽','MA_YD_10-20_GB.xlsx'),('월보','MA_YD_10-20_WB.xlsx')]
HANJA_TOK = re.compile(r'[一-鿿]{2,}')
T_HOMO = 10   # 동음이의 shortlist: 두 의미 다 이 빈도 이상


def load_text(path):
    wb = openpyxl.load_workbook(path, read_only=True); ws = wb.active
    rows = list(ws.iter_rows(values_only=True)); wb.close()
    hdr = list(rows[0])
    tc = next((hdr.index(c) for c in ('raw_text','kr_text','text') if c in hdr), None)
    lc = hdr.index('line_class') if 'line_class' in hdr else None
    out=[]
    for r in rows[1:]:
        if lc is not None and r[lc] not in ('TEXT','RTC_TEXT'): continue
        if tc is not None and r[tc]: out.append(str(r[tc]))
    return '\n'.join(out)


# --- 빈도 ---
tok_freq = Counter()
for _, fn in DBS:
    for t in HANJA_TOK.findall(load_text(OUT/fn)):
        tok_freq[t]+=1
char_freq = Counter()
for t,f in tok_freq.items():
    for c in t: char_freq[c]+=f

def read(t):
    try: return hanja.translate(t,'substitution')
    except Exception: return t

# --- 읽기 그룹 ---
reading_map = defaultdict(list)
for t in tok_freq:
    r = read(t)
    if re.search(r'[一-鿿]', r): continue
    reading_map[r].append(t)

# --- 1. 이체자 글자쌍 후보 (한 글자만 다른 동길이 단어쌍) ---
pair_contexts = defaultdict(list)   # frozenset{a,b} -> [(t1,t2), ...]
for r, toks in reading_map.items():
    if len(toks)<2: continue
    for i in range(len(toks)):
        for j in range(i+1,len(toks)):
            a,b = toks[i],toks[j]
            if len(a)!=len(b): continue
            diff=[k for k in range(len(a)) if a[k]!=b[k]]
            if len(diff)==1:
                ca,cb = a[diff[0]], b[diff[0]]
                pair_contexts[frozenset((ca,cb))].append((a,b))

variant_rows=[]; lowconf_rows=[]
char_to_canon={}
for pair, ctxs in pair_contexts.items():
    ca,cb = tuple(pair)
    # 우세형 = char_freq 큰 쪽
    if char_freq[ca]>=char_freq[cb]: canon,var = ca,cb
    else: canon,var = cb,ca
    support=len(ctxs)
    ex = '; '.join(f'{a}/{b}' for a,b in ctxs[:3])
    row = dict(variant=var, canonical=canon, var_freq=char_freq[var],
               canon_freq=char_freq[canon], support=support, examples=ex)
    if support>=2:
        variant_rows.append(row); char_to_canon[var]=canon
    else:
        lowconf_rows.append(row)

# 우세형 자체가 다른 쌍의 희소형일 수 있음 → 1회 반복 해소
for _ in range(5):
    changed=False
    for v,c in list(char_to_canon.items()):
        if c in char_to_canon and char_to_canon[c]!=c:
            char_to_canon[v]=char_to_canon[c]; changed=True
    if not changed: break

def canon_tok(t): return ''.join(char_to_canon.get(c,c) for c in t)

# --- 2. 이체자 통일 후 잔여 동음이의 ---
canon_reading=defaultdict(lambda: defaultdict(int))  # reading -> canon_tok -> freq
for t,f in tok_freq.items():
    r=read(t)
    if re.search(r'[一-鿿]', r): continue
    canon_reading[r][canon_tok(t)] += f

homo_rows=[]
for r, senses in canon_reading.items():
    big=[(tok,fr) for tok,fr in senses.items() if fr>=T_HOMO]
    if len(big)>=2:
        big.sort(key=lambda x:-x[1])
        homo_rows.append((r, big))

# --- 저장 ---
variant_rows.sort(key=lambda x:-(x['var_freq']))
with (OUT/'variant_unification_2026-05-21.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['variant','canonical','var_freq','canon_freq','support','examples']); w.writeheader()
    for row in variant_rows: w.writerow(row)
lowconf_rows.sort(key=lambda x:-(x['var_freq']))
with (OUT/'variant_lowconf_ocr_2026-05-21.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['variant','canonical','var_freq','canon_freq','support','examples']); w.writeheader()
    for row in lowconf_rows: w.writerow(row)
homo_rows.sort(key=lambda x:-sum(fr for _,fr in x[1]))
with (OUT/'homophone_shortlist_2026-05-21.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f); w.writerow(['reading','senses(tok:freq)'])
    for r,big in homo_rows: w.writerow([r, ' / '.join(f'{t}:{fr}' for t,fr in big)])

# --- 보고 ---
print('=== step 1 산출 ===')
print(f'이체자 통일 후보(support>=2): {len(variant_rows)}개 글자쌍, 영향 단어맥락 {sum(r["support"] for r in variant_rows)}')
print(f'저신뢰/OCR 의심(1회 맥락): {len(lowconf_rows)}개')
print(f'진짜 동음이의 shortlist(둘 다 freq>={T_HOMO}): {len(homo_rows)}개 읽기')
print()
print('--- 이체자 통일 상위 25 (희소형 var → 우세형 canon | var빈도/canon빈도 | 예) ---')
for r in variant_rows[:25]:
    print(f'  {r["variant"]} → {r["canonical"]}  | {r["var_freq"]}/{r["canon_freq"]} | sup={r["support"]} | {r["examples"]}')
print()
print(f'--- 진짜 동음이의 shortlist 상위 30 (둘 다 freq>={T_HOMO}) ---')
for r,big in homo_rows[:30]:
    print(f'  {r:<8} ' + ' / '.join(f'{t}:{fr}' for t,fr in big))
print()
print('--- 저신뢰(OCR 의심) 상위 12 ---')
for r in lowconf_rows[:12]:
    print(f'  {r["variant"]} → {r["canonical"]} | {r["var_freq"]}/{r["canon_freq"]} | {r["examples"]}')
print('\nCSV 3종 저장: variant_unification / variant_lowconf_ocr / homophone_shortlist (output/)')
