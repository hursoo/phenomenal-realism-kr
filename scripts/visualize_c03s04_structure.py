# -*- coding: utf-8 -*-
"""
C03-S04 구조와 차용 관계 시각화
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 데이터 정의
items = [
    ('I01', '實現思想과 人乃天', 0, '독자적', []),
    ('I02', '實在와 人乃天', 15, '차용', ['C02(14)', 'C05(1)']),
    ('I03', '汎神觀과 人乃天', 0, '독자적', []),
    ('I04', '生命과 人乃天', 5, '차용', ['C05(3)', 'C06(2)']),
    ('I05', '意識과 人乃天', 24, '차용', ['C06(21)', 'C05(1)', 'C02(1)']),
    ('I06', '靈魂과 人乃天', 10, '차용', ['C05(6)', 'C01(3)', 'C06(1)']),
    ('I07', '進化와 人乃天', 2, '차용', ['C08(2)']),
]

# 그림 생성
fig, ax = plt.subplots(figsize=(14, 10))

# 배경색
ax.set_facecolor('#f8f8f8')

# 제목
ax.text(0.5, 0.95, '『인내천요의』 제3장 제4절: 人乃天의 哲理',
        ha='center', va='top', fontsize=18, fontweight='bold',
        transform=ax.transAxes)
ax.text(0.5, 0.90, '— 논리적 구성과 『철학과 종교』 차용 관계 —',
        ha='center', va='top', fontsize=12, color='gray',
        transform=ax.transAxes)

# 각 항 박스 그리기
y_positions = np.linspace(0.78, 0.12, 7)
box_height = 0.08
box_width = 0.35

for i, (item_id, item_name, ref_count, ref_type, sources) in enumerate(items):
    y = y_positions[i]

    # 색상 결정
    if ref_type == '독자적':
        color = '#e8f5e9'  # 연한 초록
        edge_color = '#4caf50'
        label_color = '#2e7d32'
    else:
        color = '#fff3e0'  # 연한 주황
        edge_color = '#ff9800'
        label_color = '#e65100'

    # 왼쪽 박스 (항 이름)
    rect = mpatches.FancyBboxPatch((0.05, y - box_height/2), box_width, box_height,
                                    boxstyle="round,pad=0.02,rounding_size=0.02",
                                    facecolor=color, edgecolor=edge_color, linewidth=2,
                                    transform=ax.transAxes)
    ax.add_patch(rect)

    # 항 번호와 이름
    ax.text(0.07, y + 0.01, item_id, fontsize=11, fontweight='bold', color=label_color,
            transform=ax.transAxes)
    ax.text(0.12, y + 0.01, item_name, fontsize=12, fontweight='bold',
            transform=ax.transAxes)

    # 참조 쌍 개수
    if ref_count > 0:
        ax.text(0.07, y - 0.025, f'참조 쌍: {ref_count}개', fontsize=9, color='gray',
                transform=ax.transAxes)
    else:
        ax.text(0.07, y - 0.025, '참조 쌍: 0개', fontsize=9, color='gray',
                transform=ax.transAxes)

    # 오른쪽: 출처 또는 독자적 표시
    if ref_type == '독자적':
        ax.text(0.55, y, '【독자적 서술】\n천도교 고유 개념',
                fontsize=11, ha='center', va='center', color='#2e7d32',
                fontweight='bold', transform=ax.transAxes)
    else:
        # 화살표
        ax.annotate('', xy=(0.45, y), xytext=(0.42, y),
                    arrowprops=dict(arrowstyle='->', color='#ff9800', lw=2),
                    transform=ax.transAxes)

        # 출처 목록
        source_text = '차용 ← ' + ', '.join(sources)
        ax.text(0.47, y, source_text, fontsize=10, va='center',
                color='#e65100', fontweight='bold', transform=ax.transAxes)

# 범례
legend_y = 0.03
ax.add_patch(mpatches.Rectangle((0.15, legend_y), 0.03, 0.02,
             facecolor='#e8f5e9', edgecolor='#4caf50', linewidth=2,
             transform=ax.transAxes))
ax.text(0.19, legend_y + 0.01, '독자적 서술 (천도교 고유)', fontsize=10, va='center',
        transform=ax.transAxes)

ax.add_patch(mpatches.Rectangle((0.55, legend_y), 0.03, 0.02,
             facecolor='#fff3e0', edgecolor='#ff9800', linewidth=2,
             transform=ax.transAxes))
ax.text(0.59, legend_y + 0.01, '차용 (『철학과 종교』에서)', fontsize=10, va='center',
        transform=ax.transAxes)

# 축 숨기기
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')

plt.tight_layout()
plt.savefig('images/c03s04_structure_map.png', dpi=150, bbox_inches='tight',
            facecolor='white', edgecolor='none')
print('저장 완료: images/c03s04_structure_map.png')

plt.close()
