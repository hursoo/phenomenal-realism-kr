"""Cut the oldhangul-rich units of secondary sample (oldhangul_sample_wolbo18).

Article: 新年에 對ᄒᆞᆫ 新感想으로 新發明을 公告言, 李敦化, 천도교회월보 통권 18 (1912-01-15)
CNTS: CNTS-00048061346

Strategy: Path (A) — only the few units rich in old-hangul jamo are cut now,
to support Phase 2.4 (tool comparison) on the old-hangul recognition variable.
The remaining units are deferred to the canonical 75-article pipeline run.

Layout coordinates (Phase 2.1, secondary sample):
- divider y = 1190 (vs 1180 for article 01; pages are 28 px taller)
- left margin = 80
- p1 upper covers the *whole* upper band (title + author + adjacent body),
  pending user confirmation that the title-right body is part of this article.
"""
from pathlib import Path
from PIL import Image

src_dir = Path(r'C:/hp_data/0_tnt/hyeonsang/raw/journals/cheondogyo_wolbo/nl_bibliography/articles/CNTS-00048061346')
out_dir = Path(r'C:/hp_data/0_tnt/hyeonsang/_ocr_experiments/cheondogyo_wolbo_series/samples/oldhangul_sample_wolbo18/units')
out_dir.mkdir(parents=True, exist_ok=True)

units = [
    # (label,         page_filename,    x0,  y0,   x1,   y1,    role)
    ('unit_1_p1u',    'page_001.jpg',   80,   0,   563, 1190,  'left-upper: title + author (excludes prev-article tail on right)'),
    ('unit_2_p1l',    'page_001.jpg',   80, 1190,  563, 2300,  'left-lower: body start (small-glyph)'),
]

for label, fn, x0, y0, x1, y1, role in units:
    img = Image.open(src_dir / fn)
    crop = img.crop((x0, y0, x1, y1))
    out = out_dir / f'{label}.png'
    crop.save(out)
    print(f'{label:>14s}  ({x0:>4d},{y0:>4d},{x1:>4d},{y1:>4d})  size={crop.size}  -- {role}')
