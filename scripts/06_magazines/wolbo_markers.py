# -*- coding: utf-8 -*-
"""초벌 전사의 `⚠️[C:…|G:…]` 마커를 등급을 붙여 해소한다.

초벌본은 Claude·Gemini가 갈린 자리를 마커로 남겨 둔 판이다. 그대로는 문장이 읽히지
않는다. 그렇다고 한쪽을 조용히 골라 붙이면 **기계가 고른 것을 사람이 고른 것처럼**
보이게 된다. 그래서 해소하되 **어떻게 해소했는지를 글자마다 남긴다.**

등급 (`verified_transcripts/_ruleset.md` §0~§3·§8의 규약을 코드로 옮긴 것)

    규칙   두 엔진이 같거나 정자표(§3) 12쌍의 글꼴 변이·공백 차이일 뿐 — 판단이 불필요
    대장   **정본에서 사람이 똑같이 갈린 자리를 이미 결정한 적이 있다**(`marker_decisions.csv`).
           그 결정을 옮긴다. 이 자리를 본 것은 아니므로 「확인」이 아니다
    C·G    규칙 밖. 한쪽 판독을 그대로 쓴다. **기계의 선택이며 근거가 없다**
    미해소  한쪽이 15자 이상인 대분기(§8) — 문단째 갈린 자리. 고르지 않고 둘 다 남긴다
    면주   면번호·란 표시가 본문에 흘러든 것(§7). 본문에서 빼고 쪽 경계로 돌린다

이 모듈은 판단하지 않는다. 규칙 밖의 것을 규칙 안으로 끌어들이지 않는 것이 요점이다.
"""
import re

# 마커에는 `⚠️[C:x|G:y]`와 `⚠️[C:x|G:y|P:…]`(Paddle 참고값) 두 꼴이 있다.
# P를 떼지 않으면 G쪽에 `∅|P:…`가 통째로 딸려 들어와 두 판이 영영 같아지지 않는다.
MARKER = re.compile(r'⚠️\[C:(.*?)\|G:(.*?)(?:\|P:[^\]]*)?\]')
PAGENO = re.compile(r'page_number:\s*(\S+)')
BIG = 15  # §8 대분기 문턱

# _ruleset.md §3 정자표 (확정 12쌍, 화이트리스트). 이 표 밖의 한자 분쟁은 자동화 금지.
JEONGJA = {
    '教': '敎', '即': '卽', '值': '値', '概': '槪', '隷': '隸',
    '軆': '體', '躰': '體', '点': '點', '絶': '絕', '研': '硏',
    '盖': '蓋', '青': '靑', '効': '效',
}


def jeongja(s):
    return ''.join(JEONGJA.get(c, c) for c in s)


def load_ledger(path):
    """결정 대장 → {(C쪽, G쪽): 확정값}.

    `mine_marker_decisions.py`가 정본 9편에서 뽑은 「이렇게 갈렸을 때 사람은 이렇게
    정했다」의 표다. **택일이 아닌 행(`제3안`·`삭제`)과 같은 갈림이 두 값으로 정해진
    행은 뺀다.** 사람의 결정이 하나로 모이는 쌍만 옮긴다.
    """
    import collections
    import csv
    seen = collections.defaultdict(set)
    with open(path, encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            if r['verdict'] in ('C', 'G'):
                seen[(r['claude'], r['gemini'])].add(r['final'])
    return {k: next(iter(v)) for k, v in seen.items() if len(v) == 1}


def side(v):
    """∅는 「그 엔진은 아무것도 읽지 않았다」이므로 빈 문자열로 편다."""
    return '' if v == '∅' else v


def resolve(c, g, section=None, pagemap=None, ledger=None):
    """마커 한 건 → (본문에 넣을 문자열, 등급).

    등급: 규칙 · 대장 · C · G · 미해소 · 면주
    """
    raw_c, raw_g = c, g
    c, g = side(c), side(g)

    # 면번호 — 본문이 아니라 쪽 경계다. `<n>`으로 돌린다(§1의 보존 대상).
    for v in (c, g):
        m = PAGENO.search(v)
        if m:
            raw = m.group(1)
            num = (pagemap or {}).get(raw, raw)
            return f'<{num}>', '면주'

    # 면주(란 표시)가 한쪽에만 흘러든 것 — 본문에서 뺀다(§7).
    if section and {c.strip(), g.strip()} <= {section, ''} and (c or g):
        return '', '면주'

    # 정자표·공백 차이뿐이면 판단이 필요 없다(§2 '붙임 기저' · §3 정자표).
    nc, ng = re.sub(r'\s', '', jeongja(c)), re.sub(r'\s', '', jeongja(g))
    if nc == ng:
        return nc, '규칙'

    # 정본에서 사람이 같은 갈림을 이미 정한 적이 있으면 그 결정을 옮긴다.
    if ledger and (raw_c, raw_g) in ledger:
        return ledger[(raw_c, raw_g)], '대장'

    if max(len(c), len(g)) >= BIG:
        return f'〔?C:{c or "∅"}|G:{g or "∅"}〕', '미해소'

    if c:
        return c, 'C'
    if g:
        return g, 'G'
    return '', '규칙'          # 양쪽 다 ∅ — 뺄 것도 없다


GRADES = ('규칙', '대장', 'C', 'G', '미해소', '면주')


def tag(text, grade):
    """등급 표시를 붙인 본문 조각."""
    if grade in ('면주', '미해소') or not text:
        return text
    return f'{text}〔{grade}〕'


def counts(raw, section=None, pagemap=None, ledger=None):
    """전사본 한 편의 마커 등급 집계 → dict."""
    out = dict({g: 0 for g in GRADES}, 마커=0)
    for m in MARKER.finditer(raw):
        _, grade = resolve(m.group(1), m.group(2), section, pagemap, ledger)
        out['마커'] += 1
        out[grade] += 1
    return out
