# -*- coding: utf-8 -*-
"""정본이 있는 편에서 **판독들을 정본과 견준다.** 어느 판독이 얼마나 가까운가.

무엇을 재나
    정본(사람이 지면과 대조해 확정한 판)을 기준으로, 각 판독의 글자 일치율을 잰다.
    비교 대상은 `ocr/<engine>/`의 아무 폴더나 되며, 글줄 단위 재판독
    (`ocr/reread_x4/`)도 같은 형식이라 그대로 들어온다.

    띄어쓰기·쪽표시(`<n>`)·구두점은 양쪽에서 걷어 낸다 — 정본만 갖고 있는 층이라
    판독의 잘잘못이 아니다.

왜 필요한가
    「4배로 확대하면 더 잘 읽힌다」를 **한 자리의 일화가 아니라 편 전체의 수치로**
    말하기 위해서다. 표본 하나로는 그것이 운이었는지 방법이었는지 갈리지 않는다.

쓰기
    python3 score_readings.py <article_dir> <정본.md>
    python3 score_readings.py <article_dir> <정본.md> --engines claude_opus_4_7 gemini reread_x4
"""
import argparse
import difflib
import re
from pathlib import Path

COL = re.compile(r'^\[col\s*(\d+)\]\s*(.*)$', re.M)


def unit_key(p):
    m = re.search(r'unit_(\d+)', p.stem)
    return (int(m.group(1)) if m else 0, p.stem)


def engine_text(adir, engine):
    d = adir / 'ocr' / engine
    if not d.is_dir():
        return None
    out = []
    for f in sorted(d.glob('unit_*.txt'), key=unit_key):
        for m in COL.finditer(f.read_text(encoding='utf-8', errors='ignore')):
            out.append(m.group(2))
    return clean(''.join(out))


def clean(s):
    s = re.sub(r'〔면주:[^〕]*〕', '', s)
    s = re.sub(r'\[\?[^\]]*\]|\[ERROR[^\]]*\]', '', s)
    s = re.sub(r'<\d+>', '', s)
    s = re.sub(r'\[[a-z_]+\]', '', s)
    return re.sub(r'[\s.,·、。「」『』:;!?ㆍ―—\-()（）]', '', s)


def gold_text(path):
    t = path.read_text(encoding='utf-8')
    t = re.sub(r'^---\n.*?\n---\n', '', t, flags=re.S)
    t = re.sub(r'^#.*$', '', t, flags=re.M)
    i = t.find('[body]')
    if i >= 0:
        t = t[i + 6:]
    return clean(t)


def score(gold, cand):
    sm = difflib.SequenceMatcher(a=gold, b=cand, autojunk=False)
    hit = sum(n for _, _, n in sm.get_matching_blocks())
    return hit, len(gold), len(cand), sm.ratio()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('article_dir')
    ap.add_argument('gold')
    ap.add_argument('--engines', nargs='*',
                    default=['claude_opus_4_7', 'gemini', 'reread_x4'])
    args = ap.parse_args()

    adir = Path(args.article_dir)
    gold = gold_text(Path(args.gold))
    print(f'{adir.name} · 정본 {len(gold)}자\n')
    print(f"{'판독':<18}{'일치':>7}{'정본대비':>9}{'판독길이':>9}{'유사도':>8}")
    rows = []
    for e in args.engines:
        t = engine_text(adir, e)
        if t is None:
            print(f'{e:<18}   (없음)')
            continue
        hit, ng, nc, ratio = score(gold, t)
        rows.append((e, hit, ratio))
        print(f'{e:<18}{hit:>7}{100 * hit / max(1, ng):>8.1f}%{nc:>9}{ratio:>8.3f}')

    if len(rows) >= 2:
        best = max(rows, key=lambda r: r[1])
        base = [r for r in rows if r[0] == 'claude_opus_4_7']
        print(f'\n가장 가까운 판독: **{best[0]}** (일치 {best[1]}자)')
        if base and best[0] != base[0][0]:
            d = best[1] - base[0][1]
            print(f'  배치 기준(claude_opus_4_7)보다 {d:+}자 ({100 * d / max(1, base[0][1]):+.1f}%)')


if __name__ == '__main__':
    main()
