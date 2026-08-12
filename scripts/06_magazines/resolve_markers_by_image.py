# -*- coding: utf-8 -*-
"""마커가 선 자리만 골라 **지면을 다시 본다** — 글줄을 잘라 3~4배로 확대해서.

왜
    초벌의 갈린 자리(`⚠️[C:…|G:…]`)를 기계가 한쪽 골라 놓은 것이 코퍼스의 69%다
    (`TRUST.md` §2). 그 선택에는 근거가 없다. 그렇다고 전편을 다시 읽히는 것은
    글줄 단위로 5,000회가 넘는 호출이라 현실적이지 않다.

    그런데 **다시 볼 자리는 이미 알고 있다 — 마커가 선 자리다.** 마커만 골라
    그 글줄을 잘라 확대해 다시 읽히면, 전편 재판독의 몇 분의 일로 갈린 자리를 좁힌다.

    확대가 왜 필요한지는 `marker_resolution_experiment.md` §3이 실측했다. 단(段)
    이미지로는 종성(받침)이 끝내 보이지 않았고 — 단은 잘라낸 것이지 확대한 것이
    아니어서 픽셀 밀도가 같다 — **컬럼 단위로 잘라 3~4배로 넣으니 보였다.**

무엇을 하지 않는가
    이 스크립트는 **정본을 만들지 않는다.** 기계가 지면을 한 번 더 본 결과일 뿐이며,
    그 판정을 사람이 확인해야 정본이 된다. 산출 CSV의 등급을 「확인」이라 부르지 않는다.

한계 (반드시 읽을 것)
    · **마커→지면 자리잡기가 언제나 맞지는 않는다.** 면주·캡션이 글줄로 잡히거나
      판독이 글자를 빠뜨리면 조각이 밀린다. `locate()`가 쓴 닻(anchor) 길이와 중복
      후보 수를 행마다 남기므로, **닻이 짧거나 중복이 있는 행은 의심한다.**
    · 그래서 `--gold`로 정답지가 있는 편에서 먼저 점수를 재고 쓴다.

쓰기
    python3 resolve_markers_by_image.py <article_dir> --out 판정.csv
    python3 resolve_markers_by_image.py <article_dir> --gold marker_decisions.csv   # 채점
    python3 resolve_markers_by_image.py <article_dir> --limit 30 --scale 4 --window 3

의존성
    이 폴더의 다른 도구와 달리 **Anthropic API를 쓴다**(`anthropic`, `ANTHROPIC_API_KEY`).
"""
import argparse
import base64
import csv
import io
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from png_crop import read_png, write_png                        # noqa: E402
from detect_columns import (gray_profile, smooth, find_columns,  # noqa: E402
                            row_profile, find_chars, crop_scale)
from locate_marker import (MK, load_draft, unfold_c, load_cols,  # noqa: E402
                           clean, locate)

PROMPT = """너는 1910~20년대 활판 인쇄 잡지(『천도교회월보』)의 세로쓰기 국한문 지면을 판독한다.

주어지는 것은 **글줄 하나에서 잘라 확대한 조각**이다. 가운데 글자가 판정 대상이고,
두 판독 엔진이 그 자리를 서로 다르게 읽었다.

판정 규칙
1. **이미지를 근거로 고른다.** 문맥은 참고일 뿐이며, 이미지가 문맥과 어긋나면 이미지를 따른다.
2. 옛한글 자모(아래아 ㆍ, ᄒᆞ 결합형)를 현대 한글로 바꾸지 않는다.
3. **종성(받침) 유무가 가장 자주 갈리는 자리다.** 글자 아래쪽 자모가 있는지 특히 살펴라.
   ᄒᆞ / ᄒᆞᆫ / ᄒᆞᆯ / ᄒᆞᆷ 은 아래쪽 획 하나로 갈린다.
4. 둘 다 아니면 셋째 값을 적는다. 흐려서 못 고르겠으면 `?`를 적는다. **찍지 마라.**

출력은 아래 한 줄 형식만. 설명 금지.

    판정=<A|B|C:값|?> 확신=<상|중|하> 근거=<열 자 이내>"""



def _text_of(resp):
    """응답에서 **글자 블록**을 꺼낸다.

    `content[0].text`로 꺼내면 최신 모델에서 깨진다 — 첫 블록이 thinking이라
    `.text`가 없다(2026-08-12, claude-opus-5에서 실측). 블록을 훑어 text만 잇는다.
    """
    return ''.join(b.text for b in resp.content if getattr(b, 'type', '') == 'text'
                   or hasattr(b, 'text')).strip()

def crop_marker(adir, cols, draft, m, window, scale, pad=4):
    """마커 하나 → (PNG bytes, 자리 설명 dict). 실패하면 (None, dict)."""
    c = m.group(1)
    g = m.group(2).split('|P:')[0]
    tail = clean(unfold_c(draft[:m.start()]))
    head = clean(unfold_c(draft[m.end():m.end() + 90]))
    cval = '' if c == '∅' else clean(c)
    info = {'C': c, 'G': g, 'ctx_left': tail[-16:], 'ctx_right': head[:12],
            'unit': '', 'col': '', 'char': '', 'anchor': 0, 'nhits': 0, 'note': ''}

    loc, keylen, nhits = locate(cols, tail, cval, head)
    info['anchor'], info['nhits'] = keylen, nhits
    if loc is None:
        info['note'] = '자리 못 찾음'
        return None, info
    unit, colno, off = loc
    info.update(unit=unit, col=colno, char=off + 1)

    png = adir / 'units' / f'{unit}.png'
    if not png.exists():
        info['note'] = '단 이미지 없음'
        return None, info
    w, h, nch, ctype, data, plte = read_png(png)
    prof, bg, thr = gray_profile(w, h, nch, data)
    boxes_x = list(reversed(find_columns(smooth(prof))))
    if not (1 <= colno <= len(boxes_x)):
        info['note'] = f'글줄 {colno} 없음(검출 {len(boxes_x)})'
        return None, info
    a, b = boxes_x[colno - 1]
    chars = find_chars(row_profile(w, h, nch, data, a, b, thr))
    if chars:
        med = sorted(y1 - y0 for y0, y1 in chars)[len(chars) // 2]
        chars = [(y0, y1) for y0, y1 in chars if (y1 - y0) >= med * 0.55]
    if not chars:
        info['note'] = '글자 상자 없음'
        return None, info

    s = max(0, min(off, len(chars) - 1) - window)
    e = min(len(chars) - 1, min(off, len(chars) - 1) + window)
    x = max(0, a - pad); cw = min(w, b + pad) - x
    y = max(0, chars[s][0] - pad); chh = min(h, chars[e][1] + pad) - y
    buf, cw2, ch2 = crop_scale(w, h, nch, data, x, y, cw, chh, scale)
    tmp = Path(os.environ.get('TMPDIR', '/tmp')) / f'_marker_{os.getpid()}.png'
    write_png(tmp, cw2, ch2, nch, ctype, bytes(buf), plte)
    img = tmp.read_bytes()
    tmp.unlink(missing_ok=True)
    info['size'] = f'{cw2}x{ch2}'
    return img, info


def ask(client, model, img, info, window):
    q = (f"문맥:  …{info['ctx_left']} ⟦?⟧ {info['ctx_right']}…\n"
         f"A(엔진1 판독) = {info['C']}\n"
         f"B(엔진2 판독) = {info['G']}\n"
         f"조각은 글줄 {info['col']}의 {info['char']}번째 글자를 가운데 두고 "
         f"위아래 {window}자를 함께 자른 것이다. 위에서 아래로 읽는다.")
    r = client.messages.create(
        model=model, max_tokens=200, system=PROMPT,
        messages=[{'role': 'user', 'content': [
            {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png',
                                         'data': base64.b64encode(img).decode()}},
            {'type': 'text', 'text': q},
        ]}])
    return _text_of(r), r.usage.input_tokens, r.usage.output_tokens


def parse(ans):
    """모델 답 → (A/B/C:값/?, 확신, 근거).

    ⚠️ 모델은 `판정=A`라고만 쓰지 않고 `판정=A:ᆷ으`처럼 고른 값을 붙여 쓰는 일이 잦다.
    앞 글자만 보고 갈라야 한다. 이것을 놓쳐 2026-08-12 첫 채점이 0%로 나왔다 —
    모델이 틀린 것이 아니라 답을 못 읽은 것이었다.
    """
    m = re.search(r'판정=\s*([^\s]+)', ans)
    v = m.group(1) if m else '?'
    if v.startswith('A'):
        v = 'A'
    elif v.startswith('B'):
        v = 'B'
    elif v.startswith('C') and ':' in v:
        v = 'C:' + v.split(':', 1)[1]
    elif not v.startswith('?'):
        v = 'C:' + v            # 라벨 없이 값만 쓴 경우
    conf = re.search(r'확신=\s*([상중하])', ans)
    why = re.search(r'근거=\s*(.+)$', ans)
    return (v, conf.group(1) if conf else '',
            (why.group(1).strip() if why else '')[:20])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('article_dir')
    ap.add_argument('--out', default='')
    ap.add_argument('--gold', default='', help='marker_decisions.csv (채점용)')
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--window', type=int, default=3)
    ap.add_argument('--scale', type=int, default=4)
    ap.add_argument('--model', default='claude-opus-4-7')
    ap.add_argument('--engine', default='claude_opus_4_7')
    args = ap.parse_args()

    import anthropic
    key = os.environ.get('ANTHROPIC_API_KEY')
    if not key:
        env = Path('/home/creta/work/0_tnt/.env')
        if env.exists():
            for line in env.read_text(encoding='utf-8').splitlines():
                if line.startswith('ANTHROPIC_API_KEY'):
                    key = line.split('=', 1)[1].strip().strip('"\'')
    client = anthropic.Anthropic(api_key=key)

    adir = Path(args.article_dir)
    draft = load_draft(adir)
    cols = load_cols(adir, args.engine)
    ms = list(MK.finditer(draft))

    gold = {}
    if args.gold:
        with open(args.gold, encoding='utf-8-sig') as f:
            grows = [r for r in csv.DictReader(f) if r['article'] == adir.name]
        grows.sort(key=lambda r: int(r['marker_index']))
        # 🔴 번호로 맞추면 안 된다. 정답지는 **워크벤치 사본**의 마커를 센 것이고 여기서
        # 세는 것은 `articles/` 사본이라 번호가 밀린다(2026-08-12 실측: 채점 4.8%가
        # 방법의 점수가 아니라 어긋난 대조의 산물이었다). 그래서 (C쪽, G쪽) 값의
        # **차례를 정렬해** 짝을 짓는다.
        import difflib
        mine = [(m.group(1), m.group(2).split('|P:')[0]) for m in ms]
        theirs = [(r['claude'], r['gemini']) for r in grows]
        sm = difflib.SequenceMatcher(a=mine, b=theirs, autojunk=False)
        for i, j, n in sm.get_matching_blocks():
            for k in range(n):
                gold[i + k] = grows[j + k]
        print(f'정답지 {len(grows)}행 중 {len(gold)}행을 내용으로 맞췄다 '
              f'(번호가 아니라 차례로)')
    todo = sorted(gold) if gold else list(range(len(ms)))
    if args.limit:
        todo = todo[:args.limit]

    rows, tin, tout = [], 0, 0
    for k in todo:
        m = ms[k]
        img, info = crop_marker(adir, cols, draft, m, args.window, args.scale)
        rec = dict(marker_index=k, **{x: info.get(x, '') for x in
                   ('C', 'G', 'unit', 'col', 'char', 'anchor', 'nhits',
                    'ctx_left', 'ctx_right', 'note')})
        if img is None:
            rec.update(판정='', 확신='', 근거='', 값='')
        else:
            try:
                ans, i_, o_ = ask(client, args.model, img, info, args.window)
                tin += i_; tout += o_
                v, conf, why = parse(ans)
                rec.update(판정=v, 확신=conf, 근거=why,
                           값=(info['C'] if v == 'A' else info['G'] if v == 'B'
                              else v[2:] if v.startswith('C:') else ''))
            except Exception as e:                              # noqa: BLE001
                rec.update(판정='', 확신='', 근거='', 값='', note=repr(e)[:60])
        if k in gold:
            rec['정답'] = gold[k]['final']
            rec['정답유형'] = gold[k]['verdict']
        rows.append(rec)
        mark = ''
        if k in gold:
            mark = ' ✅' if rec.get('값') == gold[k]['final'] else ' ❌'
        print(f"  #{k:<4} A={info['C'][:10]:<12} B={info['G'][:10]:<12} "
              f"→ {rec.get('판정', ''):<8} {rec.get('값', '')[:10]:<12}"
              f"{('정답=' + gold[k]['final'][:10]) if k in gold else ''}{mark}", flush=True)

    out = Path(args.out) if args.out else adir / f'{adir.name}_이미지판정.csv'
    with open(out, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)

    print(f'\n{out} — {len(rows)}건 · 토큰 in={tin} out={tout} '
          f'(대략 ${tin / 1e6 * 15 + tout / 1e6 * 75:.2f})')
    if gold:
        scored = [r for r in rows if r.get('정답')]
        hit = sum(1 for r in scored if r.get('값') == r['정답'])
        ab = [r for r in scored if r.get('정답유형') in ('C', 'G')]
        abhit = sum(1 for r in ab if r.get('값') == r['정답'])
        base = sum(1 for r in scored if r['C'] == r['정답'])
        print(f"채점: 전체 {hit}/{len(scored)} ({100 * hit / max(1, len(scored)):.1f}%) · "
              f"A/B 택일만 {abhit}/{len(ab)} ({100 * abhit / max(1, len(ab)):.1f}%) · "
              f"기준선(무조건 A) {base}/{len(scored)} ({100 * base / max(1, len(scored)):.1f}%)")
        miss = [r for r in scored if r.get('값') != r['정답']]
        if miss:
            print('틀린 자리 (앞 12):')
            for r in miss[:12]:
                print(f"   #{r['marker_index']:<4} A={r['C'][:8]:<10} B={r['G'][:8]:<10} "
                      f"고름={r.get('값', '')[:8]:<10} 정답={r['정답'][:8]:<10} "
                      f"닻={r['anchor']} 중복={r['nhits']} {r.get('근거', '')}")


if __name__ == '__main__':
    main()
