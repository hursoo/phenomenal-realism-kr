"""(2) 고충실본 → (3) 현대 독해본 변환 스크립트 v1.0.

옛한글 자모 결합형을 현대 자모로 *기계적 1:1 매핑*. 한자는 그대로 보존.
띄어쓰기는 부여하지 않음 (별도 인간 단계).

매핑 정책 v1.0 (2026-05-09 Soo 결정):
- ᄒᆞ야 → 하여 (현대 표준)
- ᄋᆞㅣ → 애
- ᄒᆞᆷᄋᆞㅣ → 함이 (직역)
- ㆍ → ㅏ
- 한자 그대로 보존 (디지털 문헌학적 비교용)
- 띄어쓰기 미부여 (의미 단위 인간 부여 단계 별도)

Usage:
    python transform_old_to_modern.py <input.md> <output.md>
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

# ============================================================
# 옛한글 자모 매핑 규칙표 v0 (2026-05-09)
# ============================================================
# Order matters: longer patterns must be matched first.
# 본 1편 v1.1에서 추출한 결합형 + 표준 옛한글 매핑.

MAPPINGS_V0: list[tuple[str, str]] = [
    # ᄒᆞ + 어미 (긴 결합부터)
    ('ᄒᆞᆷᄋᆞㅣ', '함이'),     # v1.0: 一出ᄒᆞᆷᄋᆞㅣ → 일출함이 (직역)
    ('ᄒᆞ다가', '하다가'),
    ('ᄒᆞ도다', '하도다'),
    ('ᄒᆞ나니', '하나니'),
    ('ᄒᆞᄂᆞᆫ', '하는'),
    ('ᄒᆞ노니', '하노니'),
    ('ᄒᆞ니', '하니'),
    ('ᄒᆞ야', '하여'),         # v1.0: 현대 표준
    ('ᄒᆞ고', '하고'),
    ('ᄒᆞ며', '하며'),
    ('ᄒᆞ면', '하면'),
    ('ᄒᆞ나', '하나'),
    ('ᄒᆞ는', '하는'),
    ('ᄒᆞ다', '하다'),
    ('ᄒᆞ라', '하라'),
    ('ᄒᆞᆯ', '할'),
    ('ᄒᆞᆷ', '함'),
    ('ᄒᆞᆫ', '한'),
    ('ᄒᆞ던', '하던'),

    # 다른 자모 결합
    ('ᄂᆞᆫ', '는'),            # 其富ᄂᆞᆫ → 그부는
    ('ᄋᆞㅣ', '애'),            # v1.0 (단독)

    # ᄒᆞ 단독 (어미 못 잡힌 경우 fallback)
    ('ᄒᆞ', '하'),

    # 단독 옛 자모 (가장 마지막 fallback)
    ('ㆍ', 'ㅏ'),               # araea → a
]


def transform(text: str, mappings: list[tuple[str, str]] = MAPPINGS_V0) -> tuple[str, dict[str, int]]:
    """Apply old → modern mapping. Returns (transformed_text, hit_counts)."""
    counts: dict[str, int] = {}
    for old, new in mappings:
        c = text.count(old)
        if c > 0:
            text = text.replace(old, new)
            counts[old] = c
    return text, counts


def extract_body_only(raw_md: str) -> tuple[dict, str]:
    """Extract title/author/section from frontmatter + body paragraphs only.

    Returns (meta_dict, body_text). Other sections (정정 이력, 명확화 등) excluded.
    """
    # frontmatter
    parts = raw_md.split('---\n', 2)
    fm = parts[1] if len(parts) >= 3 and parts[0] == '' else ''
    rest = parts[2] if len(parts) >= 3 else raw_md

    meta = {}
    for line in fm.splitlines():
        if ':' in line and not line.startswith(' ') and not line.startswith('-'):
            k, _, v = line.partition(':')
            v = v.strip()
            # strip yaml inline comment
            if '  #' in v:
                v = v.split('  #', 1)[0].rstrip()
            elif v.endswith('#') is False and ' #' in v and not v.startswith('#'):
                # be conservative; only strip if pattern looks like comment
                pass
            meta[k.strip()] = v

    # body 영역: [body] 마커 다음 ~ 다음 ## 헤더 전까지
    m = re.search(r'\[body\]\s*\n+(.*?)(?=\n##\s|\Z)', rest, re.DOTALL)
    body_text = m.group(1).strip() if m else ''
    return meta, body_text


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    raw = src.read_text(encoding='utf-8')

    meta, body = extract_body_only(raw)
    transformed_body, counts = transform(body)

    # (3) 현대 독해본은 본문만 + 최소 메타
    out_lines = [
        '---',
        'type: transcript',
        'fidelity: modern_reading  # 층위 (3) — 옛한글 자모 → 현대 자모 기계적 변환',
        f'article_slug: {meta.get("article_slug", "")}',
        f'article_title: {meta.get("article_title", "")}',
        f'author: {meta.get("author", "")}',
        f'journal_issue: {meta.get("journal_issue", "")}',
        f'section: {meta.get("section", "")}',
        f'created: 2026-05-09',
        f'updated: 2026-05-09 (auto-generated from {src.name} via transform_old_to_modern.py v0.1)',
        f'source_high_fidelity: ../transcripts/{src.name}',
        'transform_script: transform_old_to_modern.py v0.1',
        f'mapping_hits: {sum(counts.values())} (unique patterns: {len(counts)})',
        'status: auto_generated',
        '---',
        '',
        f'# {meta.get("article_title", "")} — (3) 현대 독해본',
        '',
        f'원 자료: 「{meta.get("article_title", "")}」, {meta.get("author", "")}, {meta.get("journal_issue", "")}, {meta.get("section", "")}.',
        f'본문은 (2) 고충실본에서 옛한글 자모 → 현대 자모 기계적 변환. 한자 그대로 보존. 띄어쓰기 미부여.',
        '',
        '## 본문',
        '',
        transformed_body,
        '',
        '## 변환 요약',
        '',
    ]
    out_lines.append(f'- 매핑 패턴: {len(counts)}종 / 총 {sum(counts.values())}회')
    for old, c in sorted(counts.items(), key=lambda x: -x[1]):
        new = next(n for o, n in MAPPINGS_V0 if o == old)
        out_lines.append(f'  - `{old}` → `{new}` ({c}회)')

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text('\n'.join(out_lines) + '\n', encoding='utf-8')

    print(f'Transformed {src.name} -> {dst}')
    print(f'Mapping hits: {sum(counts.values())} ({len(counts)} unique patterns)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
