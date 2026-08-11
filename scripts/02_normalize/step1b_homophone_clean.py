"""동음이의 예외 후보 — 깨끗한 재산출 (이체자 병합 없이 원 토큰 기준).

읽기로 묶고, 2순위 의미의 빈도가 임계 이상인 읽기만 출력 → 수작업 큐레이션.
"""
import re, sys
from collections import Counter, defaultdict
from pathlib import Path
import openpyxl, hanja

sys.stdout.reconfigure(encoding='utf-8')
OUT = Path(__file__).resolve().parent.parent / 'output'
DBS = [('1915','BK_IT_1915_PR_v1.4.xlsx'),('1924','BK_YD_1924_IY_v1.3.xlsx'),
       ('개벽','MA_YD_10-20_GB.xlsx'),('월보','MA_YD_10-20_WB.xlsx')]
HANJA_TOK = re.compile(r'[一-鿿]{2,}')
T2 = 15   # 2순위 의미 최소 빈도

def load_text(path):
    wb=openpyxl.load_workbook(path,read_only=True); ws=wb.active
    rows=list(ws.iter_rows(values_only=True)); wb.close(); hdr=list(rows[0])
    tc=next((hdr.index(c) for c in ('raw_text','kr_text','text') if c in hdr),None)
    lc=hdr.index('line_class') if 'line_class' in hdr else None
    o=[]
    for r in rows[1:]:
        if lc is not None and r[lc] not in ('TEXT','RTC_TEXT'): continue
        if tc is not None and r[tc]: o.append(str(r[tc]))
    return '\n'.join(o)

tok_freq=Counter(); tok_src=defaultdict(set)
for label,fn in DBS:
    for t in HANJA_TOK.findall(load_text(OUT/fn)):
        tok_freq[t]+=1; tok_src[t].add(label)

def read(t):
    try: return hanja.translate(t,'substitution')
    except Exception: return t

grp=defaultdict(list)
for t,f in tok_freq.items():
    r=read(t)
    if re.search(r'[一-鿿]',r): continue
    grp[r].append((t,f))

cand=[]
for r,toks in grp.items():
    toks.sort(key=lambda x:-x[1])
    if len(toks)>=2 and toks[1][1]>=T2:
        cand.append((r,toks))
cand.sort(key=lambda x:-x[1][1][1])  # 2순위 빈도순

print(f'2순위 의미 빈도>={T2}인 읽기: {len(cand)}개\n')
print(f'{"읽기":<8}{"2순위freq":>9}  의미들 (토큰:빈도:소스)')
print('-'*90)
for r,toks in cand:
    parts=' / '.join(f'{t}:{f}:{"".join(sorted(tok_src[t]))}' for t,f in toks[:5])
    print(f'{r:<8}{toks[1][1]:>9}  {parts}')
