"""복구 false-positive 진단 — 고유어가 어떤 漢字 읽기로 통과했는지, 그 漢字 빈도는?

빈도 임계(漢字 형태가 충분히 빈번할 때만 SINO로 인정)로 거를 수 있는지 본다.
"""
import re, sys
from collections import Counter, defaultdict
from pathlib import Path
import openpyxl, hanja
sys.stdout.reconfigure(encoding='utf-8')
OUT = Path(__file__).resolve().parent.parent / 'output'
DBS=[('1915','BK_IT_1915_PR_v1.4.xlsx'),('1924','BK_YD_1924_IY_v1.3.xlsx'),
     ('개벽','MA_YD_10-20_GB.xlsx'),('월보','MA_YD_10-20_WB.xlsx')]
HANJA_TOK=re.compile(r'[一-鿿]{2,}'); HANGUL_RUN=re.compile(r'[가-힣]{2,}')
def load(path):
    wb=openpyxl.load_workbook(path,read_only=True);ws=wb.active
    rows=list(ws.iter_rows(values_only=True));wb.close();hdr=list(rows[0])
    tc=next((hdr.index(c) for c in('raw_text','kr_text','text') if c in hdr),None)
    lc=hdr.index('line_class') if 'line_class' in hdr else None
    return [str(r[tc]) for r in rows[1:] if (lc is None or r[lc] in('TEXT','RTC_TEXT')) and tc is not None and r[tc]]
def read(t):
    try:return hanja.translate(t,'substitution')
    except:return t
V=Counter()
texts={}
for lab,fn in DBS:
    texts[lab]=load(OUT/fn)
    for tx in texts[lab]:
        for t in HANJA_TOK.findall(tx):V[t]+=1
# 읽기 -> 받치는 漢字 토큰들(빈도)
read_to_hanja=defaultdict(list)
for t,f in V.items():
    r=read(t)
    if not re.search(r'[一-鿿]',r):read_to_hanja[r].append((t,f))
# 한글 복구 후보 빈도(개벽+월보)
rec=Counter()
for lab in('개벽','월보'):
    for tx in texts[lab]:
        for h in HANGUL_RUN.findall(tx):
            if h in read_to_hanja:rec[h]+=1
print('복구된 한글 상위 35 | 한글빈도 | 받치는 漢字(빈도) max | 받치는 漢字들')
print('-'*90)
for h,c in rec.most_common(35):
    backers=sorted(read_to_hanja[h],key=lambda x:-x[1])
    maxf=backers[0][1]
    show=' '.join(f'{t}({f})' for t,f in backers[:4])
    print(f'{h:<6}{c:>6} | max漢字={maxf:>5} | {show}')
# 빈도 임계별 SINO 크기·복구 잔존 추정
print('\n임계별: 漢字 형태 최대빈도>=th 인 복구토큰만 남길 때 (개벽+월보 복구 출현 합)')
for th in(1,3,5,10,20):
    kept=sum(c for h,c in rec.items() if max(f for _,f in read_to_hanja[h])>=th)
    print(f'  th={th:>3}: 복구 출현 {kept:>7,}')
