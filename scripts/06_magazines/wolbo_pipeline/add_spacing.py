"""(3) 현대 독해본에 Claude API로 의미 단위 띄어쓰기 부여. v1.0 (2026-05-09)

정책 v0.3 §20 띄어쓰기 정책 (3단계):
  a. 변환 단계 (transform_old_to_modern.py) — 띄어쓰기 부여 안 함
  b. Claude 의미 단위 부여 단계 — 본 스크립트 (자동)
  c. Soo 검수 단계 — 인간 검수 (스크립트 외)

규칙 (정책 v0.3 §20.b):
  - 한자 어구 단위 (循環曲線, 苦海萬頃 등)
  - 한국어 명사+조사 경계 (人이, 自身을)
  - 연결·종결어미 후 띄움 (~하여, ~로다)
  - 종결어미 후 . ? 부여
  - 한문 관용 어구 한 단위 (若之何, 樂在其中, 斷斷無二)
  - 고유 인명·지명 한 단위 (陶朱 猗頓, 倫敦伯林)
  - 삽입절·도치절 , 구분

Usage:
    python add_spacing.py <input.modern_reading.md> [<output.md>]

    출력 파일을 지정하지 않으면 입력을 in-place 갱신.
    `## 본문` 섹션 본문만 Claude API로 띄어쓰기 부여하고, 다른 섹션·메타는 보존.
"""
from __future__ import annotations
import difflib
import json
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path

# Windows 콘솔 cp949 → utf-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

ENV_PATH = Path(r'C:/hp_data/0_tnt/.env')
_env = {}
for _line in ENV_PATH.read_text(encoding='utf-8').splitlines():
    _s = _line.strip()
    if not _s or _s.startswith('#') or '=' not in _s:
        continue
    _k, _v = _s.split('=', 1)
    _env[_k.strip()] = _v.strip().strip('"').strip("'")
KEY = _env['ANTHROPIC_API_KEY']

MODEL = 'claude-opus-4-7'
ENDPOINT = 'https://api.anthropic.com/v1/messages'

SYSTEM_PROMPT = """당신은 한국 근대(1910s~1920s) 국한문혼용 잡지 텍스트의 띄어쓰기를 부여하는 전문가다.

입력 텍스트는 옛한글 자모를 현대 자모로 기계적 변환한 (3) 현대 독해본 본문이다.
띄어쓰기가 전혀 없는 상태이며, 한자는 그대로 보존되어 있다.

다음 규칙으로 의미 단위 띄어쓰기를 부여하라:

1. 한자 어구 단위로 묶기 (예: 「循環曲線」, 「苦海萬頃」, 「曲肱枕之」, 「天下同胞」, 「極樂福音」)
2. 한국어 명사+조사 경계 띄움 (예: 「人이」, 「自身을」, 「天下를」)
3. 연결어미·종결어미 후 띄움 (예: 「~하여 」, 「~하며 」, 「~로다 」, 「~지어다 」)
4. 종결어미 후 마침표 또는 물음표 부여 (「~로다.」, 「~한고?」, 「~할가?」)
5. 한문 관용 어구는 한 단위로 (「若之何」, 「樂在其中」, 「斷斷無二」, 「是何言哉」)
6. 고유 인명·지명은 각각 한 단위로 (「陶朱 猗頓」, 「秦皇 那翁」, 「倫敦伯林」, 「蓬萊方丈」)
7. 삽입절·도치절은 쉼표(,)로 구분

[엄격 제약]
- 한자는 그대로 보존, 변경·풀이 금지
- 한국어 자모도 그대로 보존, 변경 금지
- 글자 추가·삭제·재정렬 금지 (오직 공백·구두점만 추가)
- 단락 구분(빈 줄)은 입력에 있는 그대로 유지

출력은 본문 텍스트만, 추가 설명 없이 (마크다운 헤더도 없이)."""


def call_claude(body_text: str, max_tokens: int = 16000) -> tuple[str, dict]:
    payload = {
        'model': MODEL,
        'max_tokens': max_tokens,
        'system': SYSTEM_PROMPT,
        'messages': [{'role': 'user', 'content': body_text}],
    }
    data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(
        ENDPOINT,
        data=data,
        headers={
            'x-api-key': KEY,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json',
        },
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=600) as r:
        resp = json.loads(r.read().decode('utf-8'))
    blocks = resp.get('content', [])
    text = ''.join(b.get('text', '') for b in blocks if b.get('type') == 'text')
    usage = resp.get('usage', {})
    stop_reason = resp.get('stop_reason')
    if stop_reason and stop_reason != 'end_turn':
        print(f'  WARN stop_reason={stop_reason}', file=sys.stderr)
    return text, usage


def extract_body(md_text: str) -> tuple[str, str, str]:
    """Split into (head_until_body, body, tail). body = lines between '## 본문' and next '## '."""
    lines = md_text.split('\n')
    body_start = None
    body_end = None
    for i, ln in enumerate(lines):
        s = ln.strip()
        if body_start is None:
            if s.startswith('## ') and '본문' in s:
                body_start = i + 1
            continue
        if s.startswith('## '):
            body_end = i
            break
    if body_start is None:
        raise ValueError('Could not find "## 본문" section in input')
    if body_end is None:
        body_end = len(lines)

    # Strip leading/trailing blank lines from body for cleaner API input
    body_lines = lines[body_start:body_end]
    while body_lines and not body_lines[0].strip():
        body_lines = body_lines[1:]
        body_start += 1
    while body_lines and not body_lines[-1].strip():
        body_lines = body_lines[:-1]
        body_end -= 1

    head = '\n'.join(lines[:body_start]) + '\n'
    body = '\n'.join(body_lines)
    tail = '\n' + '\n'.join(lines[body_end:]) if body_end < len(lines) else ''
    return head, body, tail


def sanity_check(input_body: str, output_body: str) -> dict:
    """띄어쓰기·구두점 제거 시 두 본문이 동일해야 함 (Claude API가 글자를 변경하면 안 됨)."""
    strip = lambda s: re.sub(r'[ \t.?,!;:\n　]', '', s)
    a, b = strip(input_body), strip(output_body)
    if a == b:
        return {'identical': True, 'lcs_ratio': 1.0, 'edits': []}
    sm = difflib.SequenceMatcher(None, a, b)
    diffs = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != 'equal':
            diffs.append((tag, a[i1:i2], b[j1:j2]))
    return {'identical': False, 'lcs_ratio': sm.ratio(), 'edits': diffs}


def update_frontmatter_status(md_text: str) -> str:
    """Replace `status:` line in YAML frontmatter to indicate spacing applied."""
    lines = md_text.split('\n')
    in_fm = False
    fm_close_idx = None
    for i, ln in enumerate(lines):
        if i == 0 and ln.strip() == '---':
            in_fm = True
            continue
        if in_fm and ln.strip() == '---':
            fm_close_idx = i
            break
        if in_fm and ln.startswith('status:'):
            lines[i] = 'status: auto_with_spacing  # Claude API 의미 단위 띄어쓰기 부여, Soo 검수 대기'
        if in_fm and ln.startswith('updated:'):
            lines[i] = ln.split('(', 1)[0].rstrip() + ' (auto-spacing via add_spacing.py v1.0)'
    return '\n'.join(lines)


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2]) if len(sys.argv) >= 3 else src
    if not src.exists():
        print(f'ERROR: input not found: {src}', file=sys.stderr)
        return 1

    raw = src.read_text(encoding='utf-8')
    try:
        head, body, tail = extract_body(raw)
    except ValueError as e:
        print(f'ERROR: {e}', file=sys.stderr)
        return 1

    print(f'Input: {src}')
    print(f'Body length: {len(body)} chars')
    print(f'Calling Claude API ({MODEL})...')
    try:
        spaced, usage = call_claude(body)
    except urllib.error.HTTPError as e:
        body_err = e.read().decode('utf-8', errors='replace')[:1000]
        print(f'  ERROR HTTP {e.code} -- {body_err}', file=sys.stderr)
        return 1
    except Exception as e:
        print(f'  ERROR -- {type(e).__name__}: {e}', file=sys.stderr)
        return 1

    print(f'  input_tokens={usage.get("input_tokens")}, output_tokens={usage.get("output_tokens")}')
    print(f'  output body length: {len(spaced)} chars')

    # Sanity check: API가 글자를 변경하지 않았는지
    check = sanity_check(body, spaced)
    if check['identical']:
        print(f'  ✓ sanity check passed (chars preserved exactly)')
    else:
        print(f'  ⚠ sanity check FAILED — char-level LCS={check["lcs_ratio"]:.4f}, {len(check["edits"])} edits:', file=sys.stderr)
        for tag, a_seg, b_seg in check['edits'][:20]:
            print(f'    [{tag}] input={a_seg!r}  output={b_seg!r}', file=sys.stderr)
        print('  (Soo 검수 시 위 차이를 우선 확인)', file=sys.stderr)

    out_text = head + spaced.strip() + tail
    out_text = update_frontmatter_status(out_text)
    dst.write_text(out_text, encoding='utf-8')
    print(f'Wrote {dst}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
