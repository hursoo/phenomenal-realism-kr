"""Cut units for 「心告의 要義」 (samples/simgo_1910-11) per meta.yaml.

Source images live in 0_srh; output PNGs go to local units/.
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image
import yaml

BASE = Path(__file__).resolve().parent
META = yaml.safe_load((BASE / 'meta.yaml').read_text(encoding='utf-8'))

src_dir = Path(META['source_dir'])
units_dir = BASE / 'units'
units_dir.mkdir(parents=True, exist_ok=True)

for u in META['units']:
    page = u['page']
    x1, y1, x2, y2 = u['crop']
    img = Image.open(src_dir / page)
    crop = img.crop((x1, y1, x2, y2))
    out = BASE / u['file']
    crop.save(out, 'PNG')
    print(f"{u['id']}: {page} crop={u['crop']} -> {out.name} ({crop.size[0]}x{crop.size[1]})")
print('done.')
