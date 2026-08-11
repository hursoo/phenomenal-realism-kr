"""한글 표기 한자어 누락 편향 진단 (C단계).

목적: 현 토크나이저(漢字 2자+ 정규식)가 텍스트별로 얼마나 다른 양의
어휘를 포착하는지, 그 비대칭(편향)의 크기를 추정한다.

지표:
1) 표기 밀도 — 코퍼스별 漢字 음절 / (漢字+한글) 음절 비율
2) 포착량 — 현 토크나이저가 뽑는 漢字 2자+ 토큰 수
3) 누락 상한 — 한글 연속 어절 중 2음절+ (한자어+고유어 합산; 누락 가능 한자어의 상한)

코퍼스: 1915 이노우에 / 1924 인내천요의 / 개벽(GB) / 월보(WB)
"""
import re
import sys
from collections import Counter
from pathlib import Path

import openpyxl

sys.stdout.reconfigure(encoding='utf-8')

OUT = Path(__file__).resolve().parent.parent / 'output'

DBS = [
    ('1915 이노우에', 'BK_IT_1915_PR_v1.4.xlsx'),
    ('1924 인내천요의', 'BK_YD_1924_IY_v1.3.xlsx'),
    ('개벽 (GB)', 'MA_YD_10-20_GB.xlsx'),
    ('월보 (WB)', 'MA_YD_10-20_WB.xlsx'),
]

HANJA_CHAR = re.compile(r'[一-鿿]')
HANGUL_CHAR = re.compile(r'[가-힣]')
KANA_CHAR = re.compile(r'[ぁ-ゟ゠-ヿ]')
HANJA_TOK = re.compile(r'[一-鿿]{2,}')        # 현 토크나이저
HANGUL_RUN = re.compile(r'[가-힣]{2,}')       # 한글 연속 2음절+ (누락 후보 상한)


def get_text_col(header):
    for cand in ('raw_text', 'kr_text', 'text'):
        if cand in header:
            return header.index(cand)
    return None


def load_texts(path):
    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    header = list(rows[0])
    tc = get_text_col(header)
    lc = header.index('line_class') if 'line_class' in header else None
    texts = []
    for r in rows[1:]:
        if lc is not None and r[lc] not in ('TEXT', 'RTC_TEXT'):
            continue
        t = r[tc] if tc is not None else None
        if t:
            texts.append(str(t))
    return header, '\n'.join(texts)


print(f'{"코퍼스":<16}{"漢字음절":>9}{"한글음절":>9}{"가나":>7}{"漢字밀도":>9}{"漢字토큰종류":>11}{"漢字토큰수":>10}{"한글어절종류(2+)":>15}{"한글어절수":>10}')
print('-' * 110)

rows_out = []
for label, fname in DBS:
    header, text = load_texts(OUT / fname)
    n_hanja = len(HANJA_CHAR.findall(text))
    n_hangul = len(HANGUL_CHAR.findall(text))
    n_kana = len(KANA_CHAR.findall(text))
    density = n_hanja / (n_hanja + n_hangul) if (n_hanja + n_hangul) else 0.0
    hanja_toks = HANJA_TOK.findall(text)
    hangul_runs = HANGUL_RUN.findall(text)
    rows_out.append((label, n_hanja, n_hangul, density, len(set(hanja_toks)), len(hanja_toks), len(set(hangul_runs)), len(hangul_runs)))
    print(f'{label:<16}{n_hanja:>9,}{n_hangul:>9,}{n_kana:>7,}{density:>8.1%}{len(set(hanja_toks)):>11,}{len(hanja_toks):>10,}{len(set(hangul_runs)):>15,}{len(hangul_runs):>10,}')

print('-' * 110)
print()
print('해석 가이드:')
print('  - 漢字밀도 = 漢字음절/(漢字+한글음절). 코퍼스 간 격차가 클수록 漢字-only 자카드의 편향이 큼.')
print('  - 한글어절(2+)은 한자어+고유어 합산이라 *누락 한자어의 상한*. 실제 누락 한자어는 이보다 작음.')
print('  - 개벽/월보의 한글어절 종류 수가 漢字토큰 종류 수에 견줘 클수록, 漢字-only가 그 코퍼스 어휘를 더 많이 못 봄.')

# 개벽에서 한글어절 빈도 상위 30 — 한자어/고유어 육안 판별용
print()
print('=== 개벽(GB) 한글 연속어절(2음절+) 빈도 상위 40 — 한자어 여부 육안 판별용 ===')
_, gb_text = load_texts(OUT / 'MA_YD_10-20_GB.xlsx')
gb_runs = Counter(HANGUL_RUN.findall(gb_text))
for w, c in gb_runs.most_common(40):
    print(f'  {c:>5}  {w}')
