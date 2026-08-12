# -*- coding: utf-8 -*-
"""단 경계의 **이음매 띠**만 따로 읽어, 어긋난 자리를 메운다.

문제 (Soo 지적 → 전수 확인, 2026-08-12)
    단 분리가 `divider_y=1180` 고정값이었는데 진짜 구분선은 지면마다 다르다.
    375면을 재 보니 **92.8%가 15px 넘게, 78.4%가 40px(≈한 글자) 넘게 어긋났고
    중앙값이 −69px**다(`detect_divider.py`). 고정값이 구분선보다 위로 잡히면
    위 단은 자기 마지막 한두 글자 줄을 잃고, 그 글자들은 아래 단 이미지 맨 위에
    얹혀 **아래 단 각 컬럼의 머리에 붙어** 읽힌다. 읽는 차례가 「위 단 전 컬럼 →
    아래 단 전 컬럼」이므로 그 글자들은 제자리보다 한참 뒤에 나타난다.

    글자가 사라지는 것이 아니라 **자리를 옮긴다.** 그래서 전사본을 아무리 들여다봐도
    보이지 않는다 — 마커도 서지 않는다. 두 엔진이 같은 이미지를 받았기 때문이다.

이 스크립트가 하는 일
    지면마다 구분선을 찾아 그 **위아래 ±Δ의 띠**를 잘라 확대해 다시 읽힌다.
    띠 안에서는 구분선이 보이므로 **어느 글자가 위 단이고 어느 글자가 아래 단인지**를
    모델이 직접 가른다. 그 결과가 이음매의 정답 노릇을 한다.

    산출은 컬럼마다 한 줄이다.

        [col 01] 위: 生命은短 | 아래: ᄒᆞ니라然

    ⚠️ 이것도 **기계 판독**이다. 정본이 아니라 이음매를 고칠 근거일 뿐이다.

쓰기
    python3 read_seam.py <article_dir> [--delta 130] [--scale 3] [--dry-run]

산출: <article_dir>/ocr/seam/<page>.txt
의존성: Anthropic API + Pillow.
"""
import argparse
import base64
import io
import os
import re
import sys
import time
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from detect_divider import find_divider                       # noqa: E402

RAW = Path('/home/creta/work/0_tnt/hyeonsang/raw/journals/cheondogyo_wolbo/'
           'nl_bibliography/articles')

PROMPT = """이 이미지는 1910~20년대 활판 인쇄 잡지(『천도교회월보』)의 세로쓰기 지면에서
**단(段)을 가르는 물결 구분선의 위아래를 함께** 잘라 확대한 띠다.

이 지면은 위 단과 아래 단으로 나뉘고, 각 단 안에서 글줄은 **오른쪽에서 왼쪽으로**,
글줄 안에서는 **위에서 아래로** 읽는다. 띠 한가운데를 가로지르는 가는 물결선이 두 단의
경계다.

할 일: **글줄마다** 그 선의 위에 있는 글자와 아래에 있는 글자를 갈라 적어라.

1. 오른쪽 글줄부터 `[col 01]`, `[col 02]` … 로 번호를 매긴다.
2. 각 줄을 `[col NN] 위: … | 아래: …` 형식으로 적는다.
3. 위쪽에 글자가 없으면 `위: ∅`, 아래쪽이 없으면 `아래: ∅`.
4. 옛한글 자모(ㆍ, ᄒᆞ·ᄒᆞᆫ·ᄒᆞᆯ·ᄒᆞᆷ·ᄂᆞᆫ)를 현대 한글로 바꾸지 마라. 받침을 정확히.
5. 한자는 원본 그대로. 띄어쓰기 넣지 마라. 확실치 않으면 `[?]`.
6. 면주(欄 이름)·쪽번호가 가장자리에 보이면 `〔면주:…〕`로 감싼다.

출력은 `[col NN] …` 줄들만. 설명 금지."""



def _text_of(resp):
    """응답에서 **글자 블록**을 꺼낸다.

    `content[0].text`로 꺼내면 최신 모델에서 깨진다 — 첫 블록이 thinking이라
    `.text`가 없다(2026-08-12, claude-opus-5에서 실측). 블록을 훑어 text만 잇는다.
    """
    return ''.join(b.text for b in resp.content if getattr(b, 'type', '') == 'text'
                   or hasattr(b, 'text')).strip()

def strip_image(page, y, delta, scale, x0=60, x1=None):
    from PIL import Image
    im = Image.open(page)
    x1 = x1 or im.width
    box = (x0, max(0, y - delta), x1, min(im.height, y + delta))
    c = im.crop(box).convert('L')
    c = c.resize((c.width * scale, c.height * scale), Image.LANCZOS)
    bio = io.BytesIO()
    c.save(bio, format='PNG')
    return bio.getvalue(), box


def pages_of(adir):
    meta = yaml.safe_load((adir / 'meta.yaml').read_text(encoding='utf-8'))
    src = (meta.get('source_dir') or '').rstrip('/').split('/')[-1]
    pdir = RAW / src if (RAW / src).is_dir() else RAW / adir.name
    hgt = {p['file']: int(p['pixels'].split('x')[1])
           for p in (meta.get('source_pages') or []) if p.get('pixels')}
    out = []
    for u in (meta.get('units') or []):
        c, pg = u.get('crop'), u.get('page')
        if c and len(c) == 4 and c[1] == 0 and pg:
            if hgt.get(pg) and c[3] >= hgt[pg] - 40:
                continue                     # 단이 하나뿐인 지면 — 이음매가 없다
            f = pdir / pg
            if f.exists():
                out.append((pg, f, c[3]))
    return sorted(set(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('article_dir')
    ap.add_argument('--delta', type=int, default=130)
    ap.add_argument('--scale', type=int, default=3)
    ap.add_argument('--model', default='claude-opus-4-7')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--force', action='store_true')
    args = ap.parse_args()

    adir = Path(args.article_dir)
    pages = pages_of(adir)
    if not pages:
        print(f'{adir.name}: 이음매가 있는 지면이 없다')
        return
    out_dir = adir / 'ocr' / 'seam'

    print(f'{adir.name} · 이음매 지면 {len(pages)}')
    plans = []
    for pg, f, used in pages:
        y, h, bg = find_divider(f)
        if y is None:
            print(f'  {pg}: 구분선을 못 찾았다 — 건너뛴다')
            continue
        plans.append((pg, f, used, y))
        print(f'  {pg}  쓴값 {used} · 구분선 {y} · 어긋남 {used - y:+}px')
    if args.dry_run:
        print(f'\n예상 호출 {len(plans)}회')
        return

    import anthropic
    key = os.environ.get('ANTHROPIC_API_KEY')
    if not key:
        for line in Path('/home/creta/work/0_tnt/.env').read_text(encoding='utf-8').splitlines():
            if line.startswith('ANTHROPIC_API_KEY'):
                key = line.split('=', 1)[1].strip().strip('"\'')
    client = anthropic.Anthropic(api_key=key)
    out_dir.mkdir(parents=True, exist_ok=True)

    tin = tout = 0
    for pg, f, used, y in plans:
        dst = out_dir / f'{Path(pg).stem}.txt'
        if dst.exists() and not args.force:
            print(f'  skip {pg}')
            continue
        img, box = strip_image(f, y, args.delta, args.scale)
        txt = ''
        for attempt in range(6):
            try:
                r = client.messages.create(
                    model=args.model, max_tokens=1600, system=PROMPT,
                    messages=[{'role': 'user', 'content': [
                        {'type': 'image', 'source': {'type': 'base64',
                         'media_type': 'image/png',
                         'data': base64.b64encode(img).decode()}},
                        {'type': 'text', 'text': '이 띠의 글줄들을 위·아래로 갈라 적어라.'}]}])
                txt = _text_of(r)
                tin += r.usage.input_tokens; tout += r.usage.output_tokens
                break
            except Exception as e:                        # noqa: BLE001
                slow = 'credit balance' in str(e).lower()   # 잔액 일시 소진 — 길게 기다린다
                if attempt == 5:
                    txt = f'[ERROR {type(e).__name__}]'
                else:
                    time.sleep((60 if slow else 3) * (attempt + 1))
        head = (f'# seam read via Anthropic ({args.model})\n'
                f'# Source: {pg}  divider={y}  used={used}  offset={used - y:+}\n'
                f'# crop={box}  scale={args.scale}\n\n')
        if '[ERROR' in txt:
            print(f'  ⚠️ {pg}: 실패 — 파일을 쓰지 않는다', flush=True)
            continue
        dst.write_text(head + txt + '\n', encoding='utf-8')
        n = len(re.findall(r'^\[col', txt, re.M))
        print(f'  {pg} → 글줄 {n}줄', flush=True)
    print(f'\n{out_dir} · 토큰 in={tin} out={tout} '
          f'(대략 ${tin / 1e6 * 15 + tout / 1e6 * 75:.2f})')


if __name__ == '__main__':
    main()
