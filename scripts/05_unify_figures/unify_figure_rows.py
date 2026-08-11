# -*- coding: utf-8 -*-
"""도식 행의 line_class를 FIGURE로 통일하고 figure_path 열을 더한다.

v1.4 → v1.5 (1915) · v1.3 → v1.4 (1924)

바꾸는 것
  1. `{{FIG:...}}` 자리표시자 행의 line_class → FIGURE
     (종전: 1915는 TEXT, 1924는 ANNOTATION으로 갈렸다)
  2. 그 행에 figure_path 열을 채운다 — data/figures/의 실제 파일

바꾸지 않는 것
  - n_chunk_id. 묶음 배정은 앞 버전을 그대로 물려받는다.
    다시 자르면 묶음 수(2,195·424)와 쌍(930,680)이 바뀌어 이미 발표된
    수치와 어긋나기 때문이다.
  - 도식 안의 글자를 담은 ANNOTATION 행. 그대로 둔다.

의존성 없이 stdlib만 쓴다(xlsx = zip + xml).
"""
import zipfile, re, sys, shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape

NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / 'data' / '3_corpus'
FIGDIR = ROOT / 'data' / 'figures'

JOBS = [
    ('BK_IT_1915_PR_v1.4.xlsx', 'BK_IT_1915_PR_v1.5.xlsx', '1915', '.jpg'),
    ('BK_YD_1924_IY_v1.3.xlsx', 'BK_YD_1924_IY_v1.4.xlsx', '1924', '.png'),
]

FIG_RE = re.compile(r'\{\{FIG:\s*([^|}]+?)\s*(?:\|[^}]*)?\}\}')


def read_rows(path):
    """행 단위 [[셀값,...]] + 헤더를 반환."""
    with zipfile.ZipFile(path) as z:
        shared = []
        if 'xl/sharedStrings.xml' in z.namelist():
            root = ET.fromstring(z.read('xl/sharedStrings.xml'))
            for si in root:
                shared.append(''.join(t.text or '' for t in si.iter(NS + 't')))
        sheet = sorted(n for n in z.namelist()
                       if re.match(r'xl/worksheets/sheet\d+\.xml$', n))[0]
        root = ET.fromstring(z.read(sheet))
        out = []
        for row in root.iter(NS + 'row'):
            cells = {}
            for c in row.iter(NS + 'c'):
                ref = re.match(r'([A-Z]+)', c.get('r') or 'A').group(1)
                t = c.get('t'); v = c.find(NS + 'v'); s = ''
                if t == 's' and v is not None and v.text is not None:
                    s = shared[int(v.text)]
                elif t == 'inlineStr':
                    isel = c.find(NS + 'is')
                    if isel is not None:
                        s = ''.join(x.text or '' for x in isel.iter(NS + 't'))
                elif v is not None and v.text:
                    s = v.text
                cells[ref] = s
            out.append(cells)
        return out


def col_letter(n):
    s = ''
    while n >= 0:
        s = chr(n % 26 + 65) + s
        n = n // 26 - 1
    return s


def write_xlsx(path, header, rows):
    """인라인 문자열만 쓰는 최소 xlsx 작성기."""
    def row_xml(idx, values):
        cs = []
        for j, v in enumerate(values):
            if v is None or v == '':
                continue
            cs.append(f'<c r="{col_letter(j)}{idx}" t="inlineStr">'
                      f'<is><t xml:space="preserve">{escape(str(v))}</t></is></c>')
        return f'<row r="{idx}">' + ''.join(cs) + '</row>'

    body = [row_xml(1, header)]
    for i, r in enumerate(rows, 2):
        body.append(row_xml(i, r))
    sheet = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
             '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
             '<sheetData>' + ''.join(body) + '</sheetData></worksheet>')
    ct = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="xml" ContentType="application/xml"/>'
          '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
          '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
          '</Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            '</Relationships>')
    wb = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
          'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
          '<sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>')
    wbrels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
              '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
              '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
              '</Relationships>')
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', ct)
        z.writestr('_rels/.rels', rels)
        z.writestr('xl/workbook.xml', wb)
        z.writestr('xl/_rels/workbook.xml.rels', wbrels)
        z.writestr('xl/worksheets/sheet1.xml', sheet)


def main():
    figmap = {p.name.rsplit('_', 1)[0].split('_', 2)[2] + '|' + p.name.split('_')[0]: p.name
              for p in FIGDIR.iterdir() if p.is_file()}
    for src, dst, year, ext in JOBS:
        rows = read_rows(CORPUS / src)
        header = [rows[0].get(col_letter(i), '') for i in range(20)]
        header = [h for h in header if h]
        ncol = len(header)
        idx = {h: i for i, h in enumerate(header)}
        cls_i, txt_i = idx['line_class'], idx.get('kr_text', idx.get('raw_text'))
        pg_i = idx['page_info']

        data, changed = [], 0
        for r in rows[1:]:
            vals = [r.get(col_letter(i), '') for i in range(ncol)] + ['']
            m = FIG_RE.search(vals[txt_i] or '')
            if m:
                name = m.group(1).strip()
                page = re.match(r'(\d+)', (vals[pg_i] or '').lstrip('abc'))
                pnum = page.group(1) if page else ''
                fn = f"{year}_p{int(pnum):03d}_{name}{ext}" if pnum else ''
                if fn and (FIGDIR / fn).exists():
                    vals[cls_i] = 'FIGURE'
                    vals[-1] = f"data/figures/{fn}"
                    changed += 1
                else:
                    print(f'  ⚠️ 이미지 없음: {name} (p.{vals[pg_i]}) → {fn}')
                    vals[cls_i] = 'FIGURE'
            data.append(vals)

        write_xlsx(CORPUS / dst, header + ['figure_path'], data)
        print(f'{src} → {dst} : {len(data)}행 · FIGURE {changed}개')


if __name__ == '__main__':
    main()
