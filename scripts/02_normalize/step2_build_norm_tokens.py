"""상류 정규화 step 2 — reading-space 토큰 산출 (출현 보존).

규칙 (normalization_spec_2026-05-21.md):
  漢字 토큰(2자+):
    - EXCLUDE 셋  -> 드롭
    - EXCEPTION 셋 -> 漢字 그대로 유지(읽기 변환 면제)
    - 그 외        -> 한국 한자음(한글)으로 변환
  한글 어절(2자+):
    - 읽기가 EXCEPTION 읽기  -> 드롭(모호)
    - 읽기가 한자어 읽기집합  -> 그 한글 유지(한자어 복구)
    - 그 외                  -> 드롭(고유어)
  가나: 무시.

산출: output/norm/tokens_<src>.csv  (src, n_chunk_id, c, token) — 출현당 1행.
보고: 복구/제외/유지 통계.
"""
import csv, re, sys
from collections import Counter, defaultdict
from pathlib import Path
import openpyxl, hanja

sys.stdout.reconfigure(encoding='utf-8')
OUT = Path(__file__).resolve().parent.parent / 'output'
NORM = OUT / 'norm'; NORM.mkdir(exist_ok=True)
DBS = [('1915','BK_IT_1915_PR_v1.4.xlsx'),('1924','BK_YD_1924_IY_v1.3.xlsx'),
       ('개벽','MA_YD_10-20_GB.xlsx'),('월보','MA_YD_10-20_WB.xlsx')]
HANJA_TOK = re.compile(r'[一-鿿]{2,}')
HANGUL_RUN = re.compile(r'[가-힣]{2,}')

EXCEPTION = set('理想 以上 主義 注意 朝鮮 祖先 自身 自信 植物 食物 家庭 假定 調和 造化 婦人 否認 夫人 神聖 神性 定義 正義 一切 一節 東洋 同樣 歐洲 九州 神道 信徒 印度 人道 引導 一身 一神 起源 祈願 現象 現狀 神人 新人 孔丘 攻究'.split())
EXCLUDE = set('其人 幾人 其者 一大 幾分 一一 此二'.split())

def read(t):
    try: return hanja.translate(t,'substitution')
    except Exception: return t

def load_rows(path):
    wb=openpyxl.load_workbook(path,read_only=True); ws=wb.active
    rows=list(ws.iter_rows(values_only=True)); wb.close(); hdr=list(rows[0])
    tc=next((hdr.index(c) for c in ('raw_text','kr_text','text') if c in hdr),None)
    lc=hdr.index('line_class') if 'line_class' in hdr else None
    nc=hdr.index('n_chunk_id') if 'n_chunk_id' in hdr else None
    out=[]
    for r in rows[1:]:
        if lc is not None and r[lc] not in ('TEXT','RTC_TEXT'): continue
        nid = r[nc] if nc is not None else None
        txt = r[tc] if (tc is not None and r[tc]) else ''
        out.append((nid, str(txt)))
    return out

# --- V & 사전 (전 소스 漢字 토큰 읽기) ---
allrows={lab:load_rows(OUT/fn) for lab,fn in DBS}
V=Counter()
for lab,rows in allrows.items():
    for _,txt in rows:
        for t in HANJA_TOK.findall(txt): V[t]+=1
tok_read={t:read(t) for t in V}
SINO_READINGS={r for r in tok_read.values() if not re.search(r'[一-鿿]',r)}
EXC_READINGS={tok_read.get(t,read(t)) for t in EXCEPTION}

# 게이트: 읽기별 漢字 형태 최대빈도 vs 한글 어절 빈도.
# 漢字형태가 한글형태만큼 빈번할 때만 한자어로 인정(native 동음 배제).
_hanja_maxf=defaultdict(int)
for _t,_f in V.items():
    _r=tok_read[_t]
    if not re.search(r'[一-鿿]',_r): _hanja_maxf[_r]=max(_hanja_maxf[_r],_f)
hangul_freq=Counter()
for _lab,_rows in allrows.items():
    for _,_txt in _rows:
        for _h in HANGUL_RUN.findall(_txt): hangul_freq[_h]+=1
GATED_SINO={r for r in SINO_READINGS if _hanja_maxf[r]>=hangul_freq.get(r,0)}

# --- 토큰화 ---
def norm_tokens(txt):
    """반환: (tokens, stat) — tokens는 출현 리스트."""
    toks=[]; st=Counter()
    for t in HANJA_TOK.findall(txt):
        if t in EXCLUDE: st['hanja_excluded']+=1; continue
        if t in EXCEPTION: toks.append(t); st['hanja_exception']+=1; continue
        toks.append(tok_read.get(t, read(t))); st['hanja_converted']+=1
    for h in HANGUL_RUN.findall(txt):
        if h in EXC_READINGS: st['hangul_dropped_ambig']+=1; continue
        if h in GATED_SINO: toks.append(h); st['hangul_recovered']+=1
        else: st['hangul_dropped_native']+=1
    return toks, st

print(f'{"src":<6}{"漢字변환":>9}{"漢字예외":>9}{"漢字제외":>9}{"한글복구":>9}{"한글드롭(고유)":>13}{"한글드롭(모호)":>13}{"총토큰":>9}')
print('-'*82)
TOTAL=Counter()
for lab,rows in allrows.items():
    rowstat=Counter(); ntok=0
    out_rows=[]
    for nid,txt in rows:
        toks,st=norm_tokens(txt); rowstat+=st; ntok+=len(toks)
        c = str(nid).split('-')[0] if nid else ''
        for tk in toks: out_rows.append((lab,nid,c,tk))
    with (NORM/f'tokens_{lab}.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f); w.writerow(['src','n_chunk_id','c','token']); w.writerows(out_rows)
    TOTAL+=rowstat
    print(f'{lab:<6}{rowstat["hanja_converted"]:>9,}{rowstat["hanja_exception"]:>9,}{rowstat["hanja_excluded"]:>9,}'
          f'{rowstat["hangul_recovered"]:>9,}{rowstat["hangul_dropped_native"]:>13,}{rowstat["hangul_dropped_ambig"]:>13,}{ntok:>9,}')
print('-'*82)
print(f'{"합계":<6}{TOTAL["hanja_converted"]:>9,}{TOTAL["hanja_exception"]:>9,}{TOTAL["hanja_excluded"]:>9,}'
      f'{TOTAL["hangul_recovered"]:>9,}{TOTAL["hangul_dropped_native"]:>13,}{TOTAL["hangul_dropped_ambig"]:>13,}')

# 한글 복구 토큰 빈도 상위 — 한자어 맞는지 육안 점검
print('\n=== 복구된 한글-한자어 빈도 상위 30 (개벽+월보) — 진짜 한자어인지 점검 ===')
rec=Counter()
for lab in ('개벽','월보'):
    for nid,txt in allrows[lab]:
        for h in HANGUL_RUN.findall(txt):
            if h not in EXC_READINGS and h in GATED_SINO: rec[h]+=1
for w,c in rec.most_common(30):
    print(f'  {c:>5}  {w}')
print(f'\n토큰 테이블 저장: {NORM}/tokens_*.csv')
