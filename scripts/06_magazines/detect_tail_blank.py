# -*- coding: utf-8 -*-
"""**마지막 지면의 끝이 비었나** — 받지 않고 가려내려 한 1차 체. 🔴 **졌다. 쓰지 않는다.**

결과 먼저
    아는 답 아홉 편으로 자를 재어 보니 **틀렸다.** 다음 쪽으로 넘어간 것이 확실한
    C34(0.379)·C36(0.403)이 둘 다 「끝남」으로 나왔다. 아홉 중 여덟이 「끝남」이니
    가르는 힘이 없다.

    까닭이 분명하다. **월보는 한 지면의 상단과 하단에 서로 다른 글을 앉힌다.**
    C30의 27쪽이 그랬다 — 상단이 「最高消遣法」의 끝이고 하단은 이미 다음 글
    「天人의 欲能者一本」이다. 그러니 하단 왼쪽의 여백은 **다음 글이 얼마나
    찼는가**를 말할 뿐 이 글의 끝과는 상관이 없다.

    아래 전제 자체가 틀렸다 — 「글이 그 지면에서 끝났다면 하단 왼쪽에 빈 글줄이
    남는다」. 글은 **상단에서 끝날 수 있다.**

    확실한 길은 `fetch_next_article_pages.py`다 — 다음 글의 첫 지면을 받아 그 위를 본다.
    아래는 실패한 길의 기록으로 남긴다. **같은 착상이 다시 떠오를 때 읽으라고 둔다.**

--- 아래는 처음 적었던 설명 ---

왜
    `audit_article_end.py`가 81편을 「다음지면필요」로 남겼다. 그 81편의 끝을 알려면
    다음 글의 첫 지면을 받아야 하는데, **81번 받기 전에 공짜로 가릴 수 있는 몫이 있다.**

    세로쓰기는 오른쪽에서 왼쪽으로 읽는다. 그러니 **글이 그 지면에서 끝났다면 하단
    왼쪽에 빈 글줄이 남는다.** 반대로 왼쪽 끝까지 글자가 찼다면 이야기가 다음 쪽으로
    넘어갔을 공산이 크다. 잉크만 세면 되고, 판독도 통신도 필요 없다.

무엇을 재나
    마지막 보유 지면의 **하단(구분선 아래)** 에서, 왼쪽 여백(면주·쪽번호가 앉는 자리)을
    뺀 안쪽 띠의 잉크 비율을 잰다. `detect_divider.py`가 찾은 구분선을 그대로 쓴다.

        빈칸비율 ≥ 0.35   → `끝남` — 하단 왼쪽이 비었다. 그 지면에서 끝났다고 본다
        빈칸비율 ≤ 0.05   → `참`   — 왼쪽 끝까지 글자가 찼다. **다음 지면을 받아야 한다**
        그 사이            → `애매` — 사람이 본다

한계
    - **이것도 선별기다.** 글이 마지막 글줄을 꽉 채우고 끝나는 일은 얼마든지 있다.
      `참`은 「넘어갔다」가 아니라 「받아 봐야 안다」다.
    - 사진·표·삽화가 하단에 앉으면 잉크가 엉뚱하게 잡힌다. 그런 편은 `애매`로 떨어진다.
    - 다단 조판이 아닌 지면(한 면에 한 란만 있는 경우)에서는 구분선이 없어 `구분선없음`.

쓰기
    python3 detect_tail_blank.py                  # audit의 「다음지면필요」 전부
    python3 detect_tail_blank.py --series 34,36   # 아는 답으로 자를 검사할 때
"""
import argparse
import csv
import re
from pathlib import Path

import yaml
from PIL import Image

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from detect_divider import find_divider  # noqa: E402

WB = Path('/home/creta/work/0_tnt/hyeonsang/_ocr_experiments/cheondogyo_wolbo_series')
RAW = Path('/home/creta/work/0_tnt/hyeonsang/raw/journals/cheondogyo_wolbo/'
           'nl_bibliography/articles')
REPO = Path(__file__).resolve().parents[2] / 'data' / '5_magazine_sources' / 'wolbo'

MARGIN = 0.055   # 면주·쪽번호가 앉는 바깥 여백. 재지 않는다
BAND = 0.22      # 하단 왼쪽에서 이만큼을 본다
INK = 0.10       # 한 세로줄이 「글자가 있다」고 볼 잉크 비율


def page_dir(slug):
    d = WB / 'articles' / slug
    mp = d / 'meta.yaml'
    if not mp.exists():
        return None
    meta = yaml.safe_load(mp.read_text(encoding='utf-8'))
    src = (meta.get('source_dir') or '').rstrip('/').split('/')[-1]
    for cand in (RAW / src, RAW / slug):
        if cand.is_dir():
            return cand
    return None


def blank_ratio(img_path):
    """하단 왼쪽 띠에서 **빈 세로줄의 비율**을 돌려준다. PIL만 쓴다."""
    im = Image.open(img_path).convert('L')
    w, h = im.size
    y, _h, _bg = find_divider(img_path)
    if y is None or h - y < 100:
        return None, y
    px = im.load()
    samp = sorted(px[x, yy] for x in range(0, w, 17) for yy in range(y, h, 17))
    if not samp:
        return None, y
    bg = samp[len(samp) // 2]
    thr = max(90, int(bg * 0.72))                     # 종이색에서 떨어진 값만 잉크
    x0, x1 = int(w * MARGIN), int(w * (MARGIN + BAND))
    if x1 <= x0:
        return None, y
    rows = list(range(y, h, 3))
    blank = 0
    for x in range(x0, x1):
        n = sum(1 for yy in rows if px[x, yy] < thr)
        if n / len(rows) < INK:
            blank += 1
    return blank / (x1 - x0), y


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--series', default='')
    args = ap.parse_args()

    ap_csv = REPO / 'article_end_audit.csv'
    if not ap_csv.exists():
        raise SystemExit('먼저 audit_article_end.py 를 돌린다')
    audit = {int(r['series']): r for r in csv.DictReader(ap_csv.open(encoding='utf-8-sig'))}

    if args.series:
        want = [int(s) for s in args.series.split(',')]
    else:
        want = [s for s, r in audit.items() if r['verdict'] == '다음지면필요']

    dirs = {}
    for d in sorted((WB / 'articles').iterdir()):
        m = re.match(r'(\d+)_', d.name)
        if d.is_dir() and m:
            dirs[int(m.group(1))] = d.name

    out = []
    for s in sorted(want):
        slug = dirs.get(s)
        r = audit.get(s, {})
        rec = {'series': s, 'slug': slug or '', 'title': r.get('title', ''),
               'tonggwon': r.get('tonggwon', ''), 'last_held': r.get('last_held', ''),
               'next_page': r.get('next_page', ''), 'blank': '', 'divider_y': '',
               'verdict': ''}
        pd_ = page_dir(slug) if slug else None
        if not pd_:
            rec['verdict'] = '지면못찾음'
        else:
            jpgs = sorted(pd_.glob('*.jpg'))
            if not jpgs:
                rec['verdict'] = '지면못찾음'
            else:
                try:
                    b, y = blank_ratio(jpgs[-1])
                except Exception as e:                     # noqa: BLE001
                    b, y = None, None
                    rec['verdict'] = f'오류:{type(e).__name__}'
                if b is None and not rec['verdict']:
                    rec['verdict'] = '구분선없음'
                elif b is not None:
                    rec['blank'] = round(b, 3)
                    rec['divider_y'] = y
                    rec['verdict'] = ('끝남' if b >= 0.35 else
                                      '참' if b <= 0.05 else '애매')
        out.append(rec)
        print(f"  #{rec['series']:<4} {str(rec['title'])[:18]:<20} 빈칸 "
              f"{rec['blank'] if rec['blank'] != '' else '—':>5}  {rec['verdict']}")

    p = REPO / 'tail_blank_screen.csv'
    with p.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader(); w.writerows(out)

    tally = {}
    for r in out:
        tally[r['verdict']] = tally.get(r['verdict'], 0) + 1
    print(f'\n{len(out)}편 → {p.name}')
    for k in sorted(tally, key=lambda k: -tally[k]):
        print(f'  {k:<10} {tally[k]:>4}')


if __name__ == '__main__':
    main()
