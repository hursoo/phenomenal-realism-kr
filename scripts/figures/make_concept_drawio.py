# -*- coding: utf-8 -*-
"""간이 개념 흐름도 → 인내천논증_개념도.drawio (draw.io에서 열어 손보기용).

make_concept.py(matplotlib 판)와 같은 구조를 draw.io XML로 생성. draw.io에서 열어
문구·배치·색을 직접 편집하고 고해상 PNG/PDF로 export하면 된다.
출력: appendix/인내천논증_개념도.drawio
"""
import xml.sax.saxutils as su
from pathlib import Path

OUT = Path(__file__).parent.parent / "appendix"

S = {
    'src':   'rounded=1;whiteSpace=wrap;html=1;fillColor=#fde9d9;strokeColor=#c0504d;fontSize=13;verticalAlign=middle;',
    'norm':  'rounded=1;whiteSpace=wrap;html=1;fillColor=#ece8f6;strokeColor=#7a6cae;fontSize=13;verticalAlign=middle;',
    'blue':  'rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=13;verticalAlign=middle;',
    'green': 'rounded=1;whiteSpace=wrap;html=1;fillColor=#e2efda;strokeColor=#82a878;fontSize=13;verticalAlign=middle;',
    'fig':   'rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;fontSize=13;verticalAlign=middle;',
    'out':   'rounded=1;whiteSpace=wrap;html=1;fillColor=#dbe5f1;strokeColor=#4f81bd;fontSize=13;verticalAlign=middle;',
    'region':'rounded=0;whiteSpace=wrap;html=1;fillColor=#f4f4f6;strokeColor=#c9c9d2;verticalAlign=top;fontStyle=1;fontSize=15;spacingTop=6;spacingLeft=8;',
}

# (id, value, x, y, w, h, style)  — 뒤(region) → 앞(node) 순
NODES = [
    ('RG21', '2.1  경로의 발견', 40, 180, 840, 560, 'region'),
    ('RG22', '2.2', 255, 795, 410, 120, 'region'),

    ('N1', '<b>자료와 가공</b><br>이노우에 1915 · 이돈화 잡지(개벽·월보) · 이돈화 1924<br>→ 정규화 · 문장 묶음(자료 간 단위 통일)',
     160, 40, 600, 84, 'src'),
    ('N2', '<b>양 끝점 어휘 친화 측정</b><br>1915와 1924를 <i>양쪽 모두</i> 얼마나 닮았나<br>직접(1915→1924)  vs  매개(잡지 경유)',
     260, 210, 400, 84, 'norm'),
    ('N3a', '<b>갈래 A · 경로 비교</b><br><br>매개가 직접보다 상위에서 우세<br>→ 어휘는 집중된 굴절',
     95, 380, 300, 104, 'blue'),
    ('N3b', '<b>갈래 B · 주요 매개 글</b><br><br>양 끝을 잇는 매개 클러스터<br>개벽 C53·C22·C43·C19 + 월보 C72',
     520, 380, 330, 104, 'green'),
    ('N4', '<b>경로 = 집중된 굴절 → 회수</b><br>(그림 2: 어휘 친화 네트워크)',
     255, 570, 410, 80, 'fig'),
    ('N5', '<b>번안 양상</b><br>소거 ⊂ 회수',
     320, 810, 280, 80, 'out'),
]
EDGES = [('N1', 'N2'), ('N2', 'N3a'), ('N2', 'N3b'),
         ('N3a', 'N4'), ('N3b', 'N4'), ('N4', 'N5')]

e = 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;strokeColor=#4a5568;strokeWidth=1.6;fontSize=10;'
esc = su.escape
cells = ['<mxCell id="0"/>', '<mxCell id="1" parent="0"/>']
for nid, val, x, y, w, h, st in NODES:
    cells.append(f'<mxCell id="{nid}" value="{esc(val)}" style="{S[st]}" vertex="1" parent="1">'
                 f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
for i, (s, t) in enumerate(EDGES):
    cells.append(f'<mxCell id="e{i}" style="{e}" edge="1" parent="1" source="{s}" target="{t}">'
                 f'<mxGeometry relative="1" as="geometry"/></mxCell>')

xml = ('<mxfile host="app.diagrams.net"><diagram name="concept" id="concept">'
       '<mxGraphModel dx="900" dy="1000" grid="1" gridSize="10" guides="1" tooltips="1" '
       'connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="900" pageHeight="980" '
       'math="0" shadow="0"><root>' + ''.join(cells) + '</root></mxGraphModel></diagram></mxfile>')
(OUT / '인내천논증_개념도.drawio').write_text(xml, encoding='utf-8')
print(f"saved {OUT / '인내천논증_개념도.drawio'}")
