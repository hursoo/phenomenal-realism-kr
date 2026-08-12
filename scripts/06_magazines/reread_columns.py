# -*- coding: utf-8 -*-
"""글줄(段의 컬럼) 하나씩 3~4배로 확대해 다시 읽힌다 — 정본화의 셋째 판독.

왜
    배치 판독은 단(段) 이미지를 통째로 넣는다. 단은 지면을 **잘라낸 것이지 확대한 것이
    아니어서** 글자당 픽셀 수가 지면과 같고, 그래서 종성(받침)이 보이지 않는다
    (`marker_resolution_experiment.md` §3). 글줄 하나만 잘라 4배로 넣으면 보인다.

    마커 자리를 **글자 단위로 겨누는 방식은 실패했다**(§8-1, C30 채점 A/B 1/9로 기준선
    이하). 자리잡기가 병목이었다. **글줄 단위는 겨눌 것이 없다** — 컬럼 상자만 잡으면
    되고 그것은 `detect_columns.py`가 안정적으로 한다. 이 스크립트가 그 방식이다.

무엇이 되고 무엇이 안 되나
    ✅ 종성 — §8-2에서 배치가 「死ᄒᆞ而已」로 읽은 자리를 4배가 「死ᄒᆞᆯ而已」로 읽었고
       정본과 일치했다.
    ❌ 한자 혼동 — 같은 자리에서 `怠`를 두 판독 모두 `息`으로 읽었다. **확대는 종성을
       살리고 한자 혼동은 남긴다.** 그래서 이것은 정본이 아니라 **셋째 의견**이다.

쓰기
    python3 reread_columns.py <article_dir>                 # 전 단
    python3 reread_columns.py <article_dir> --unit unit_1_p1u --scale 4
    python3 reread_columns.py <article_dir> --dry-run       # 컬럼 수·비용만

산출
    <article_dir>/ocr/reread_x4/<unit>.txt   — 엔진 출력과 같은 `[col NN]` 형식이라
    기존 도구(`consensus.py`·`locate_marker.py`)가 그대로 읽는다.

의존성
    Anthropic API(`anthropic`) + Pillow. 이 폴더의 다른 도구와 달리 의존성이 있다.
"""
import argparse
import base64
import io
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from png_crop import read_png                                  # noqa: E402
from detect_columns import gray_profile, smooth, find_columns   # noqa: E402

PROMPT = """이 이미지는 1910~20년대 활판 인쇄 잡지(『천도교회월보』)의 세로쓰기 국한문
지면에서 **글줄 하나**를 잘라 확대한 것이다. 위에서 아래로 한 글자씩 읽어라.

1. 옛한글 자모(아래아 ㆍ, ᄒᆞ·ᄒᆞᆫ·ᄒᆞᆯ·ᄒᆞᆷ·ᄂᆞᆫ 결합형)를 **현대 한글로 바꾸지 마라.**
2. **받침 유무를 특히 정확히 보라.** ᄒᆞ / ᄒᆞᆫ / ᄒᆞᆯ / ᄒᆞᆷ 은 아래 획 하나로 갈린다.
   이 판독을 하는 목적이 그것이다.
3. 한자는 원본 그대로(정자·속자 구분 없이). 확실하지 않은 글자는 `[?]`로 둔다.
4. 띄어쓰기를 넣지 마라. 원문에 없다.
5. 면주(欄 이름)·쪽번호가 글줄에 섞여 있으면 `〔면주:…〕`로 감싸 본문과 구분하라.

출력은 판독한 글자열 한 줄만. 설명·해석 금지."""



def _text_of(resp):
    """응답에서 **글자 블록**을 꺼낸다.

    `content[0].text`로 꺼내면 최신 모델에서 깨진다 — 첫 블록이 thinking이라
    `.text`가 없다(2026-08-12, claude-opus-5에서 실측). 블록을 훑어 text만 잇는다.
    """
    return ''.join(b.text for b in resp.content if getattr(b, 'type', '') == 'text'
                   or hasattr(b, 'text')).strip()

def split_wide(boxes, factor=1.6, prof=None):
    """중앙값보다 훨씬 넓은 상자를 **글줄 수만큼 균등 분할**한다.

    글줄 사이 여백이 좁거나 잉크가 번지면 `find_columns`가 여러 글줄을 한 상자로
    묶는다. C30 `unit_5_p3u`에서 실측한 폭은
    `[48, 48, 48, 47, 46, 41, 509, 48, 48, 47]` — **509px 상자 하나가 열 글줄을
    삼켰다.** 그 상자를 통째로 잘라 넣으면 모델이 여러 글줄을 뒤섞어 읽거나
    일부를 건너뛴다. 정본 대조에서 「다然ᄒᆞ나如何ᄒᆞᆫ糟粕일」 한 토막이 통째로
    빠진 것이 이 때문이다(2026-08-12).

    균등 분할은 근사다. 글줄 간격이 고른 활판이라 대체로 맞지만, 어긋나면 조각이
    옆 글줄을 물게 된다. 그래도 **한 상자에 열 글줄을 넣는 것보다는 낫다.**
    """
    if len(boxes) < 3:
        return boxes
    widths = sorted(b - a for a, b in boxes)
    med = widths[len(widths) // 2]
    if med <= 0:
        return boxes
    out = []
    for a, b in boxes:
        w = b - a
        k = int(round(w / med))
        if w > med * factor and k >= 2:
            cuts = _valleys(prof, a, b, k, med) if prof else []
            if len(cuts) == k - 1:
                edges = [a] + cuts + [b]
                out += [(edges[i], edges[i + 1]) for i in range(k)]
            else:                                  # 골을 못 찾으면 균등 분할
                step = w / k
                out += [(int(a + i * step), int(a + (i + 1) * step)) for i in range(k)]
        else:
            out.append((a, b))
    return out


def _valleys(prof, a, b, k, med):
    """상자 안에서 **잉크가 가장 옅은 자리** k−1곳을 찾는다.

    균등 분할은 글줄 간격이 고를 때만 맞고, 표제처럼 글자가 큰 상자를 반으로
    잘라 버릴 수 있다. 상자 안의 실제 여백에서 쪼개는 편이 안전하다.
    """
    cuts, banned = [], set()
    span = list(range(a + int(med * 0.5), b - int(med * 0.5)))
    for _ in range(k - 1):
        cand = [x for x in span if x not in banned]
        if not cand:
            return []
        x = min(cand, key=lambda i: prof[i] if i < len(prof) else 1 << 30)
        cuts.append(x)
        banned |= set(range(x - int(med * 0.6), x + int(med * 0.6)))
    return sorted(cuts)


def columns_of(png, min_width=18, do_split=False):
    w, h, nch, ctype, data, plte = read_png(png)
    prof, bg, thr = gray_profile(w, h, nch, data)
    sm = smooth(prof)
    boxes = list(reversed(find_columns(sm)))               # 오른쪽=1번
    boxes = [(a, b) for a, b in boxes if b - a >= min_width]
    if do_split:
        boxes = split_wide(boxes, prof=sm)
    return boxes, (w, h)


def crop_x(png, a, b, scale, pad=6):
    from PIL import Image
    im = Image.open(png)
    x0, x1 = max(0, a - pad), min(im.width, b + pad)
    c = im.crop((x0, 0, x1, im.height))
    c = c.resize((c.width * scale, c.height * scale), Image.LANCZOS)
    bio = io.BytesIO()
    c.save(bio, format='PNG')
    return bio.getvalue()


def engine_cols(adir, unit):
    """두 엔진이 그 단에서 읽은 글줄들 — 후보로 줄 때 쓴다."""
    out = {}
    for eng, lab in (('claude_opus_4_7', 'A'), ('gemini', 'B')):
        f = adir / 'ocr' / eng / f'{unit}.txt'
        if not f.exists():
            continue
        for m in re.finditer(r'^\[col\s*(\d+)\]\s*(.*)$',
                             f.read_text(encoding='utf-8', errors='ignore'), re.M):
            out.setdefault(int(m.group(1)), {})[lab] = re.sub(r'\s', '', m.group(2))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('article_dir')
    ap.add_argument('--unit', default='')
    ap.add_argument('--scale', type=int, default=4)
    ap.add_argument('--model', default='claude-opus-4-7')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--force', action='store_true')
    ap.add_argument('--with-candidates', action='store_true',
                    help='두 엔진의 그 글줄 판독을 후보로 함께 준다(중재 방식). '
                         '어제 실험에서 후보를 주면 음절·한자 판별이 크게 올랐다')
    ap.add_argument('--split-wide', action='store_true',
                    help='넓은 상자를 글줄 수만큼 쪼갠다. 기본은 끔 — C30 실측에서 '
                         '88.7퍼센트가 79.3퍼센트로 떨어졌다')
    ap.add_argument('--tag', default='',
                    help='산출 폴더 이름 꼬리표 (ocr/reread_x4<tag>/)')
    args = ap.parse_args()

    adir = Path(args.article_dir)
    units = sorted((adir / 'units').glob('*.png'))
    if args.unit:
        units = [u for u in units if u.stem == args.unit]
    if not units:
        sys.exit(f'단 이미지가 없다: {adir}/units/')
    out_dir = adir / 'ocr' / f'reread_x{args.scale}{args.tag}'

    plan = []
    for u in units:
        cols, size = columns_of(u, do_split=args.split_wide)
        plan.append((u, cols, size))
    total = sum(len(c) for _, c, _ in plan)
    print(f'{adir.name} · 단 {len(plan)} · 글줄 {total} · ×{args.scale}')
    for u, cols, size in plan:
        print(f'  {u.stem:<16} {size[0]}x{size[1]}  글줄 {len(cols)}')
    if args.dry_run:
        print(f'\n예상 호출 {total}회 · 대략 ${total * 0.07:.2f}')
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
    for u, cols, _ in plan:
        dst = out_dir / f'{u.stem}.txt'
        if dst.exists() and not args.force:
            print(f'  skip {u.stem}')
            continue
        lines = [f'# reread x{args.scale} via Anthropic ({args.model}) — 글줄 단위 재판독',
                 f'# Source: {u.name}  columns={len(cols)}', '']
        cand = engine_cols(adir, u.stem) if args.with_candidates else {}
        for i, (a, b) in enumerate(cols, 1):
            img = crop_x(u, a, b, args.scale)
            ask = '이 글줄을 판독하라.'
            if cand.get(i):
                c = cand[i]
                ask += ('\n\n참고 — 다른 두 판독이 이 글줄을 이렇게 읽었다. '
                        '**맞는지 이미지로 확인하고, 틀린 자리는 고쳐라.** '
                        '둘 다 틀렸으면 네 판독을 써라.\n'
                        f"  A: {c.get('A', '(없음)')}\n  B: {c.get('B', '(없음)')}")
            for attempt in range(6):
                try:
                    r = client.messages.create(
                        model=args.model, max_tokens=700, system=PROMPT,
                        messages=[{'role': 'user', 'content': [
                            {'type': 'image', 'source': {'type': 'base64',
                             'media_type': 'image/png', 'data': base64.b64encode(img).decode()}},
                            {'type': 'text', 'text': ask}]}])
                    txt = (_text_of(r).splitlines() or [''])[0].strip()
                    tin += r.usage.input_tokens; tout += r.usage.output_tokens
                    break
                except Exception as e:                       # noqa: BLE001
                    # 잔액이 일시적으로 비는 일이 있다(자동 충전이 따라오기 전).
                    # 그때는 **오래 기다렸다 다시 건다.** 짧게 세 번 재고 포기하면
                    # 파일에 [ERROR]가 박히고, 채점은 그것을 「모델이 못 읽은 자리」로
                    # 세어 그럴듯한 나쁜 점수를 만든다(2026-08-12에 두 번 겪었다).
                    slow = 'credit balance' in str(e).lower()
                    if attempt == 5:
                        txt = f'[ERROR {type(e).__name__}]'
                    else:
                        time.sleep((60 if slow else 3) * (attempt + 1))
            lines.append(f'[col {i:02d}] {txt}')
            print(f'  {u.stem} col{i:02d}  {txt[:44]}', flush=True)
        # 절반 넘게 실패했으면 **쓰지 않는다.** 빈 자리로 남아야 눈에 띈다.
        bad = sum(1 for x in lines if '[ERROR' in x)
        if cols and bad > len(cols) / 2:
            print(f'  ⚠️ {u.stem}: {bad}/{len(cols)} 실패 — 파일을 쓰지 않는다', flush=True)
            continue
        dst.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'\n{out_dir} · 토큰 in={tin} out={tout} '
          f'(대략 ${tin / 1e6 * 15 + tout / 1e6 * 75:.2f})')


if __name__ == '__main__':
    main()
