"""step 3 — norm_tokens로 변②③ β·γ 재산출 후 기존(漢字-only) 대비 비교.

β·γ 정의는 compute_jaccard_3edges_v2.py와 동일:
  잡지 글의 각 N: j15=max jac vs 1915 N, j24=max jac vs 1924 N, F1=조화평균.
  글 β=max F1, γ=mean F1.
토큰만 norm_tokens(output/norm/tokens_*.csv)로 교체(set-자카드, 문장 묶음 단위 dedupe).

비교: 매개 클러스터(C53·C43·C22·C19·C23)+상위권의 β·γ·z·순위가 어떻게 바뀌나.
"""
import csv, statistics, sys
from collections import defaultdict
from pathlib import Path
import openpyxl
sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(__file__).resolve().parent.parent
NORM = BASE / 'output' / 'norm'
OUT = BASE / 'output'
OLD_CSV = OUT / 'jaccard_3edges_v2_2026-05-19.csv'
SRC2DB = {'1915':'BK_IT_1915_PR','1924':'BK_YD_1924_IY','개벽':'MA_YD_10-20_GB','월보':'MA_YD_10-20_WB'}
CLUSTER = {('MA_YD_10-20_GB',c) for c in ('C53','C43','C22','C19','C23')}

def jac(a,b):
    if not a or not b: return 0.0
    return len(a&b)/len(a|b)
def f1(a,b):
    return 0.0 if (a<=0 or b<=0) else 2*a*b/(a+b)

# --- norm 토큰 로드 (set per n_chunk) ---
def load_norm(src):
    by_id=defaultdict(set); by_c=defaultdict(list); seen=set()
    with (NORM/f'tokens_{src}.csv').open(encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            by_id[row['n_chunk_id']].add(row['token'])
    for nid in sorted(by_id):
        c=str(nid).split('-')[0]
        if (c,nid) not in seen:
            by_c[c].append(nid); seen.add((c,nid))
    return dict(by_id), dict(by_c)

norm={s:load_norm(s) for s in SRC2DB}
id1915=norm['1915'][0]; id1924=norm['1924'][0]
chunks_1915=list(id1915.items()); chunks_1924=list(id1924.items())
print(f'1915 N={len(chunks_1915)} · 1924 N={len(chunks_1924)} · 개벽 N={len(norm["개벽"][0])} · 월보 N={len(norm["월보"][0])}')

# --- 메타(title/date) ---
def load_meta(fn):
    wb=openpyxl.load_workbook(OUT/fn,read_only=True);ws=wb.active
    rows=list(ws.iter_rows(values_only=True));wb.close();hdr=list(rows[0])
    import json
    lid=hdr.index('local_id'); mc=hdr.index('src_metadata') if 'src_metadata' in hdr else None
    meta={}
    if mc is None: return meta
    for r in rows[1:]:
        l=r[lid]
        if not l or '-' not in str(l): continue
        c=str(l).split('-')[0]
        if c in meta or not r[mc]: continue
        try: meta[c]=json.loads(r[mc])
        except: pass
    return meta
meta={'MA_YD_10-20_GB':load_meta('MA_YD_10-20_GB.xlsx'),'MA_YD_10-20_WB':load_meta('MA_YD_10-20_WB.xlsx')}

# --- β·γ 재산출 ---
res={}
for src,db in (('개벽','MA_YD_10-20_GB'),('월보','MA_YD_10-20_WB')):
    by_id,by_c=norm[src]
    for c,nids in by_c.items():
        fs=[]
        for nid in nids:
            t=by_id[nid]
            j15=max((jac(t,x[1]) for x in chunks_1915),default=0.0)
            j24=max((jac(t,x[1]) for x in chunks_1924),default=0.0)
            fs.append(f1(j15,j24))
        if not fs: continue
        res[(db,c)]={'beta':max(fs),'gamma':statistics.mean(fs),'n':len(nids)}

def zstats(key):
    vals=[v[key] for v in res.values()]
    return statistics.mean(vals),statistics.stdev(vals),vals
mb,sb,_=zstats('beta'); mg,sg,_=zstats('gamma')
for k,v in res.items():
    v['zb']=(v['beta']-mb)/sb; v['zg']=(v['gamma']-mg)/sg
rank_b={k:i for i,k in enumerate(sorted(res,key=lambda k:-res[k]['beta']),1)}
rank_g={k:i for i,k in enumerate(sorted(res,key=lambda k:-res[k]['gamma']),1)}

# --- 기존 CSV 로드 ---
old={}
with OLD_CSV.open(encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        old[(row['db_id'],row['c'])]={'beta':float(row['beta_F1_max']),'gamma':float(row['gamma_F1_mean']),
                                       'title':row.get('title',''),'date':row.get('date','')}
ob_sorted=sorted(old,key=lambda k:-old[k]['beta']); og_sorted=sorted(old,key=lambda k:-old[k]['gamma'])
old_rb={k:i for i,k in enumerate(ob_sorted,1)}; old_rg={k:i for i,k in enumerate(og_sorted,1)}
ovb=[old[k]['beta'] for k in old]; ovg=[old[k]['gamma'] for k in old]
omb,osb=statistics.mean(ovb),statistics.stdev(ovb); omg,osg=statistics.mean(ovg),statistics.stdev(ovg)

def title(k):
    m=meta.get(k[0],{}).get(k[1],{})
    return (m.get('title') or old.get(k,{}).get('title') or '')[:24]

print(f'\n=== 신규(norm) β 분포: mean={mb:.4f} sd={sb:.4f} max={max(v["beta"] for v in res.values()):.4f} | '
      f'기존: mean={omb:.4f} sd={osb:.4f} ===')
print('\n=== 신규 β 상위 15 (c | 신규 β·z·순위 | 기존 β·z·순위 | 제목) ===')
for k in sorted(res,key=lambda k:-res[k]['beta'])[:15]:
    o=old.get(k); oz=(o['beta']-omb)/osb if o else float('nan'); orank=old_rb.get(k,'-')
    star='★' if k in CLUSTER else ' '
    print(f' {star}{k[0][-2:]} {k[1]:>4} | β={res[k]["beta"]:.4f} z={res[k]["zb"]:+.2f} #{rank_b[k]:<3} | '
          f'old β={o["beta"]:.4f} z={oz:+.2f} #{orank:<3} | {title(k)}' if o else
          f' {star}{k[0][-2:]} {k[1]:>4} | β={res[k]["beta"]:.4f} #{rank_b[k]} | (기존 없음)')

print('\n=== 매개 클러스터 5글: 기존 → 신규 (β 순위·z) ===')
print(f'{"c":>6} {"제목":<22} | {"old βrank(z)":>14} | {"new βrank(z)":>14} | {"old γrank":>9} {"new γrank":>9}')
for k in sorted(CLUSTER,key=lambda k:rank_b.get(k,999)):
    if k not in res: print(f'{k[1]:>6} (신규 결과 없음)'); continue
    o=old.get(k); oz=(o['beta']-omb)/osb if o else 0
    print(f'{k[1]:>6} {title(k):<22} | #{old_rb.get(k,"-"):>3}({oz:+.2f}) | #{rank_b[k]:>3}({res[k]["zb"]:+.2f}) | '
          f'#{old_rg.get(k,"-"):>7} #{rank_g[k]:>7}')

# 상위 10 멤버십 변동
new_top10=set(sorted(res,key=lambda k:-res[k]['beta'])[:10])
old_top10=set(ob_sorted[:10])
print(f'\n=== β 상위10 멤버십 변동 ===')
print(f'  기존 top10: {[k[1] for k in ob_sorted[:10]]}')
print(f'  신규 top10: {[k[1] for k in sorted(res,key=lambda k:-res[k]["beta"])[:10]]}')
print(f'  유지: {sorted(k[1] for k in new_top10&old_top10)} | 진입: {sorted(k[1] for k in new_top10-old_top10)} | 이탈: {sorted(k[1] for k in old_top10-new_top10)}')

with (OUT/'jaccard_3edges_norm_2026-05-21.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f); w.writerow(['db_id','c','n','beta','gamma','zb','zg','rank_b','rank_g','old_beta','old_rank_b'])
    for k in sorted(res,key=lambda k:-res[k]['beta']):
        o=old.get(k,{})
        w.writerow([k[0],k[1],res[k]['n'],f'{res[k]["beta"]:.6f}',f'{res[k]["gamma"]:.6f}',
                    f'{res[k]["zb"]:.3f}',f'{res[k]["zg"]:.3f}',rank_b[k],rank_g[k],
                    o.get('beta',''),old_rb.get(k,'')])
print(f'\nCSV: {OUT}/jaccard_3edges_norm_2026-05-21.csv')
