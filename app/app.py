import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import re


# =============================================================================
# [캐싱 함수] 데이터 로딩 성능 최적화
# =============================================================================

@st.cache_data
def load_excel(file_path: str, header: int = 0) -> pd.DataFrame:
    """엑셀 파일을 캐싱하여 로드합니다."""
    if os.path.exists(file_path):
        return pd.read_excel(file_path, header=header)
    return pd.DataFrame()


@st.cache_data
def load_csv(file_path: str) -> pd.DataFrame:
    """CSV 파일을 캐싱하여 로드합니다."""
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    return pd.DataFrame()


@st.cache_data
def load_text_preview(file_path: str, limit_lines: int = 100) -> tuple:
    """텍스트 파일을 캐싱하여 로드합니다."""
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
        preview_lines = all_lines[:limit_lines]
        txt_content = "".join(preview_lines)
        if len(all_lines) > limit_lines:
            txt_content += f"\n\n[전체 {len(all_lines)}줄 중 앞부분 {limit_lines}줄만 표시]"
        return txt_content, len(all_lines)
    return "", 0


# =============================================================================
# [섹션 로딩 및 렌더링]
# =============================================================================

SECTIONS_DIR = os.path.join(os.path.dirname(__file__), "sections")


def load_section(filename: str) -> str:
    """sections/ 폴더에서 마크다운 파일을 읽어 반환합니다."""
    path = os.path.join(SECTIONS_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def render_section(content: str, components: dict):
    """마크다운 내 <!-- component: name --> 마커를 기준으로 분할하여 렌더링합니다."""
    parts = re.split(r'<!-- component: (\w+) -->', content)
    for i, part in enumerate(parts):
        if i % 2 == 0:  # 텍스트
            text = part.strip()
            if text:
                st.markdown(text, unsafe_allow_html=True)
        else:  # 컴포넌트 이름
            if part in components:
                components[part]()


# =============================================================================
# [시각화 함수]
# =============================================================================

def create_philosophy_rank_chart() -> go.Figure:
    """'哲學' 순위 차이를 보여주는 꺾은선 차트"""
    words = ['哲學', '宗敎', '生命', '進化', '眞理']
    rank_1915 = [8, 1, 3, 116, 260]
    rank_1924 = [518, 11, 2, 8, 31]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        name='1915 철학과 종교',
        x=words,
        y=rank_1915,
        mode='lines+markers+text',
        line=dict(color='#4A90A4', width=3),
        marker=dict(size=12, symbol='circle'),
        text=[f'{r}위' for r in rank_1915],
        textposition='top center',
        textfont=dict(size=11, color='#4A90A4'),
        hovertemplate='<b>%{x}</b><br>1915 순위: %{y}위<extra></extra>'
    ))

    fig.add_trace(go.Scatter(
        name='1924 인내천요의',
        x=words,
        y=rank_1924,
        mode='lines+markers+text',
        line=dict(color='#E07B54', width=3),
        marker=dict(size=12, symbol='diamond'),
        text=[f'{r}위' for r in rank_1924],
        textposition='bottom center',
        textfont=dict(size=11, color='#E07B54'),
        hovertemplate='<b>%{x}</b><br>1924 순위: %{y}위<extra></extra>'
    ))

    fig.add_annotation(
        x='哲學', y=260,
        text="<b>510계단 차이</b>",
        showarrow=True,
        arrowhead=2,
        arrowsize=1.5,
        arrowwidth=2,
        arrowcolor='#D9534F',
        ax=0, ay=-40,
        font=dict(size=12, color='#D9534F'),
        bgcolor='rgba(255,255,255,0.8)',
        bordercolor='#D9534F',
        borderwidth=1
    )

    fig.update_layout(
        title=dict(text="주요 개념어 순위 대조", font=dict(size=16)),
        xaxis_title='개념어',
        yaxis_title='순위 (낮을수록 빈도 높음)',
        yaxis=dict(autorange='reversed', range=[0, 550]),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
        height=500,
        margin=dict(t=80, b=60),
        hovermode='x unified'
    )

    return fig


def create_chapter_distribution_chart() -> go.Figure:
    """1924 텍스트 장별 참조쌍 분포 차트"""
    chapters = ['C01 緖言', 'C02 天道', 'C03 眞理', 'C04 目的', 'C05 修煉', 'C06 雜感']
    counts = [3, 0, 45, 0, 0, 63]
    colors = ['#95a5a6', '#95a5a6', '#3498db', '#95a5a6', '#95a5a6', '#e74c3c']

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=chapters,
        y=counts,
        marker_color=colors,
        text=counts,
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>유효 쌍: %{y}개<extra></extra>'
    ))

    fig.update_layout(
        title=dict(text="1924 텍스트 장별 유효 참조쌍 분포 (총 111개)", font=dict(size=16)),
        yaxis_title='참조쌍 개수',
        height=400,
        margin=dict(t=60, b=40)
    )

    return fig


# =============================================================================
# [컴포넌트 함수] 각 섹션에서 사용되는 테이블/차트/이미지
# =============================================================================

# --- Ⅱ-1. 문단별 데이터 ---

def render_corpus_table():
    df = pd.DataFrame({
        '텍스트': ['『철학과 종교』', '『인내천요의』', '**비율 (1915:1924)**'],
        '원저자': ['이노우에 데츠지로', '이돈화', ''],
        '간행년': ['1915', '1924', ''],
        '행 수': ['11,088', '2,254', '**4.9:1**'],
        '문단 수': ['626', '366', '**1.7:1**'],
        '한자어 토큰': ['39,938', '15,868', '**2.5:1**']
    })
    st.table(df)


def render_paragraph_table():
    df = pd.DataFrame({
        '텍스트': ['1915 철학과 종교', '1924 인내천요의'],
        '문단 수': ['626개', '366개'],
        '문단당 평균 한자어 종류': ['**40.2종**', '**31.7종**']
    })
    st.table(df)
    st.caption("*주: 자카드 유사도는 집합 연산이므로, 중복을 제거한 고유 단어 종류(types)를 기준으로 산출한다.*")


# --- Ⅱ-2. 공통 한자어 비율 ---

def render_stats_table():
    df = pd.DataFrame({
        '통계량': ['평균 (μ)', '표준편차 (σ)', '중앙값', 'P99', 'P99.94 (135개)'],
        '값': ['0.005', '0.013', '0.000', '0.048', '0.100']
    })
    st.table(df)


def render_common_tokens_table():
    df = pd.DataFrame({
        '문단A 종류': ['10종', '20종', '**40종**'],
        '문단B 종류': ['10종', '20종', '**32종**'],
        '필요 공통 종류': ['최소 2종', '최소 4종', '**최소 7종**']
    })
    st.table(df)


def render_range_table():
    df = pd.DataFrame({
        '유사도 구간': ['0.10~0.149', '0.15~0.199', '0.20 이상', '**합계**'],
        '쌍 수': ['76개', '32개', '27개', '**135개**']
    })
    st.table(df)


def render_valid_pairs_table():
    df = pd.DataFrame({
        '구분': ['초기 후보', '노이즈 (서수)', '노이즈 (범용어)', '**유효 쌍**'],
        '개수': ['135개', '-7개', '-17개', '**111개**']
    })
    st.table(df)


# --- Ⅲ-1. 분포와 특징 ---

def render_chapter_dist_table():
    df = pd.DataFrame({
        '1924 장': ['C01', 'C02', 'C03', 'C04', 'C05', 'C06', '**합계**'],
        '제목': ['緖言', '人乃天과 天道', '人乃天과 眞理', '人乃天의 目的', '人乃天의 修煉', '人乃天에 對한 雜感', ''],
        '유효 쌍': ['3개', '0개', '45개', '0개', '0개', '63개', '**111개**'],
        '비율': ['3%', '0%', '41%', '0%', '0%', '57%', '**100%**']
    })
    st.table(df)


def render_chapter_dist_chart():
    fig = create_chapter_distribution_chart()
    st.plotly_chart(fig, use_container_width=True)


def render_heatmap():
    col1, col2, col3 = st.columns([1, 6, 1])
    with col2:
        heatmap_path = os.path.join(os.path.dirname(__file__), "..", "images", "chapter_heatmap_avg_above_threshold.png")
        if os.path.exists(heatmap_path):
            st.image(heatmap_path, caption="그림 1. 장-장 단위 유효 참조쌍 분포 (111개, 자카드 유사도 ≥ 0.1). 색상은 참조쌍 개수, 괄호 안은 평균 유사도.")
        else:
            alt_path = os.path.join(os.path.dirname(__file__), "..", "images", "chapter_heatmap_avg_above_threshold.png")
            if os.path.exists(alt_path):
                st.image(alt_path, caption="그림 1. 장-장 단위 유효 참조쌍 분포")
            else:
                st.info("히트맵 이미지 파일을 찾을 수 없습니다.")


def render_ref_table():
    df = pd.DataFrame({
        '1915 장': ['C02 (현상즉실재론)', 'C06 (의식론)', 'C13 (기독교와 유교)', 'C14 (불교와 기독교)'],
        '1924 장': ['C03 (人乃天과 眞理)', 'C03 (人乃天과 眞理)', 'C06 (人乃天에 對한 雜感)', 'C06 (人乃天에 對한 雜感)'],
        '쌍 수': ['13개', '24개', '31개', '20개'],
        '내용': ['唯物/唯心→實在 논증', '헤켈 6종 의식론', '儒基 비교 프레임', '佛基 비교 프레임']
    })
    st.table(df)


def render_c03s04_table():
    df = pd.DataFrame({
        '항': ['I01', '**I02**', 'I03', 'I04', '**I05**', 'I06', 'I07'],
        '제목': ['實現思想과 人乃天', '**實在와 人乃天**', '汎神觀과 人乃天', '生命과 人乃天', '**意識과 人乃天**', '靈魂과 人乃天', '進化와 人乃天'],
        '참조쌍': ['0개', '**13개**', '0개', '5개', '**21개**', '4개', '1개'],
        '참조 원천 (1915)': ['-', 'C02 (현상즉실재론)', '-', 'C05 (생명론)', 'C06 (의식론)', 'C05 (생명론)', 'C08 (진화론)']
    })
    st.table(df)


def render_c06s06_table():
    df = pd.DataFrame({
        '1915 장': ['C13 (기독교와 유교)', 'C14 (불교와 기독교)'],
        '1924 절': ['C06-S06', 'C06-S06'],
        '쌍 수': ['31개', '20개'],
        '비교 항목': ['信仰/德敎, 創造/發展, 復活, 兼愛/差別愛', '沒我敎/主我敎, 涅槃/天國, 汎神/一神']
    })
    st.table(df)


# --- Ⅲ-2. 보편화와 비교 ---

def render_borrow_table():
    df = pd.DataFrame({
        '차용된 내용': ['현상즉실재론 (C02)', '헤켈 의식론 (C06)', '생명론 (C05)', '儒基/佛基 비교 프레임 (C13-14)'],
        '차용되지 않은 내용': ['일본 국체론 (C24-28)', '일본 신도론 (C25)', '일본 불교 우월론', '일본 중심주의']
    })
    st.table(df)


def render_invert_table():
    df = pd.DataFrame({
        '비교 항목': ['沒我敎/主我敎', '汎神敎/一神敎', '唯物/唯心'],
        '이노우에의 평가': ['불교의 특성으로 제시', '종교 유형 분류', '실재론으로 지양'],
        '이돈화의 활용': ['인내천은 이 구분을 초월', '인내천은 양자를 종합', '인내천으로 지양']
    })
    st.table(df)


# --- Ⅳ-1. 철학 기표 소거 ---

def render_phil_freq_table():
    df = pd.DataFrame({
        '텍스트': ['1915 철학과 종교', '1924 인내천요의'],
        "'哲學' 순위": ['**8위**', '**518위**'],
        '빈도': ['365회', '6회'],
        '상대빈도(‰)': ['9.14‰', '0.38‰']
    })
    st.table(df)


def render_rank_chart():
    fig = create_philosophy_rank_chart()
    st.plotly_chart(fig, use_container_width=True)


def render_inverse_table():
    df = pd.DataFrame({
        '항': ['I02', 'I05', 'I07'],
        '제목': ['實在와 人乃天', '意識과 人乃天', '進化와 人乃天'],
        '참조쌍': ['**13개**', '**21개**', '1개'],
        "'哲學' 출현": ['**0회**', '**0회**', '3회']
    })
    st.table(df)


def render_paradox_image():
    col1, col2, col3 = st.columns([1, 6, 1])
    with col2:
        paradox_path = os.path.join(os.path.dirname(__file__), "..", "images", "c03s04_philosophy_paradox.png")
        if os.path.exists(paradox_path):
            st.image(paradox_path, caption="그림 2. C03-S04 항별 참조쌍 개수(막대)와 '哲學' 출현 빈도(선). 참조 밀도가 높은 I02, I05에서 '哲學'은 0회.")
        else:
            alt_path = os.path.join(os.path.dirname(__file__), "..", "images", "c03s04_philosophy_paradox.png")
            if os.path.exists(alt_path):
                st.image(alt_path, caption="그림 2. C03-S04 항별 참조쌍 개수와 '哲學' 출현 빈도의 역상관")


# --- Ⅳ-2. 철리 인내천 ---

def render_sub_stats_table():
    df = pd.DataFrame({
        '구분': ['1915에 \'哲學\' 포함 참조쌍', '그 중 1924에도 \'哲學\' 있음', '**1924에서 \'哲學\' 소거됨**'],
        '개수': ['5개', '1개', '**4개**']
    })
    st.table(df)


def render_pattern_table():
    df = pd.DataFrame({
        '패턴': ['**A**', '**B**', '**C**'],
        '1915 원어': ['哲學的價値, 哲學系統', '哲學宗敎의 特色', '哲學宗敎의 特色'],
        '1924 대체어': ['哲人 + 眞理', '理想의 境涯', '沒我敎/主我敎'],
        '전략': ['학문 체계 → 행위자 + 목표', '학문적 범주 → 도달해야 할 경지', '학문적 분류 → 종교 내적 명명']
    })
    st.table(df)


# --- 부록 ---

def render_file_table():
    df = pd.DataFrame({
        '파일': [
            'data/analysis/validated_pairs_final.csv',
            'data/analysis/word_rank_1915.csv',
            'data/analysis/word_rank_1924.csv',
            'data/analysis/c03s04_item_analysis.csv',
            'data/analysis/philosophy_substitution_patterns.csv'
        ],
        '내용': [
            '111개 유효 참조쌍',
            '1915 텍스트 한자어 순위',
            '1924 텍스트 한자어 순위',
            'C03-S04 항별 분석',
            '대체어 패턴'
        ]
    })
    st.table(df)


def render_pairs_data():
    pairs_path = os.path.join(os.path.dirname(__file__), "..", "data", "analysis", "validated_pairs_final.csv")
    df_pairs = load_csv(pairs_path)

    if not df_pairs.empty:
        display_cols = ['rank', 'similarity', 'pid_1915', 'pid_1924', 'common_tokens']
        available_cols = [c for c in display_cols if c in df_pairs.columns]
        if available_cols:
            st.dataframe(df_pairs[available_cols].head(20), height=500)
        else:
            st.dataframe(df_pairs.head(20), height=500)
    else:
        df_top = pd.DataFrame({
            '순위': [1, 2, 3, 4, 5],
            '유사도': [0.3077, 0.2500, 0.2500, 0.2500, 0.2500],
            '1915 문단': ['C13-S01-P05', 'C02-P29', 'C06-P17', 'C13-S03-P02', 'C14-S03-P01'],
            '1924 문단': ['C06-S06-P06', 'C03-S04-I02-P01', 'C03-S04-I05-P03', 'C06-S06-P02', 'C06-S06-P09'],
            '공통 토큰': ['復活, 基督, 基督敎, 儒敎', '唯物論, 唯心論, 實在論', '意識, 本位, 細胞', '基督敎, 儒敎, 差異點', '佛敎, 基督敎, 宗敎']
        })
        st.table(df_top)
        st.caption("*전체 111개 참조쌍은 data/analysis/validated_pairs_final.csv 참조*")


# =============================================================================
# 페이지 기본 설정
# =============================================================================

st.set_page_config(
    page_title="디지털 문헌학: 현상즉실재론의 유입",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 다운로드 툴바 숨기기
st.markdown("""
    <style>
    [data-testid="stElementToolbar"] { display: none; }
    </style>
    """, unsafe_allow_html=True)


# =============================================================================
# 사이드바 목차
# =============================================================================

st.sidebar.title("목차")
selection = st.sidebar.radio(
    "이동하기",
    [
        "Ⅰ. 머리말",
        "Ⅱ. DB 구축과 다국어 비교 방법",
        "　　1. 문단별 데이터를 비교 단위로",
        "　　2. 공통 한자어 비율을 계산",
        "Ⅲ. 취사선택 양상과 특징",
        "　　1. 실재, 의식 및 종교 비교",
        "　　2. 보편화하기와 비교하기",
        "Ⅳ. 철학 개념을 다루는 방식",
        "　　1. 철학적이지만 '철학'은 회피",
        "　　2. 哲理로서의 인내천",
        "Ⅴ. 맺음말",
        "부록"
    ]
)


# =============================================================================
# 섹션별 컴포넌트 매핑
# =============================================================================

COMPONENTS_02_1 = {
    "corpus_table": render_corpus_table,
    "paragraph_table": render_paragraph_table,
}

COMPONENTS_02_2 = {
    "stats_table": render_stats_table,
    "common_tokens_table": render_common_tokens_table,
    "range_table": render_range_table,
    "valid_pairs_table": render_valid_pairs_table,
}

COMPONENTS_03_1 = {
    "chapter_dist_table": render_chapter_dist_table,
    "chapter_dist_chart": render_chapter_dist_chart,
    "heatmap": render_heatmap,
    "ref_table": render_ref_table,
    "c03s04_table": render_c03s04_table,
    "c06s06_table": render_c06s06_table,
}

COMPONENTS_03_2 = {
    "borrow_table": render_borrow_table,
    "invert_table": render_invert_table,
}

COMPONENTS_04_1 = {
    "phil_freq_table": render_phil_freq_table,
    "rank_chart": render_rank_chart,
    "inverse_table": render_inverse_table,
    "paradox_image": render_paradox_image,
}

COMPONENTS_04_2 = {
    "sub_stats_table": render_sub_stats_table,
    "pattern_table": render_pattern_table,
}

COMPONENTS_06 = {
    "file_table": render_file_table,
    "pairs_data": render_pairs_data,
}


# =============================================================================
# Ⅰ. 머리말
# =============================================================================

if selection == "Ⅰ. 머리말":
    content = load_section("01_머리말.md")
    render_section(content, {})


# =============================================================================
# Ⅱ. 연구 설계
# =============================================================================

elif selection in ["Ⅱ. DB 구축과 다국어 비교 방법", "　　1. 문단별 데이터를 비교 단위로", "　　2. 공통 한자어 비율을 계산"]:
    st.header("Ⅱ. DB 구축과 다국어 비교 방법")

    if selection in ["Ⅱ. DB 구축과 다국어 비교 방법", "　　1. 문단별 데이터를 비교 단위로"]:
        content = load_section("02-1_문단별_데이터.md")
        render_section(content, COMPONENTS_02_1)

    if selection in ["Ⅱ. DB 구축과 다국어 비교 방법", "　　2. 공통 한자어 비율을 계산"]:
        content = load_section("02-2_공통_한자어_비율.md")
        render_section(content, COMPONENTS_02_2)


# =============================================================================
# Ⅲ. 취사선택 양상과 특징
# =============================================================================

elif selection in ["Ⅲ. 취사선택 양상과 특징", "　　1. 실재, 의식 및 종교 비교", "　　2. 보편화하기와 비교하기"]:
    st.header("Ⅲ. 취사선택 양상과 특징")

    if selection in ["Ⅲ. 취사선택 양상과 특징", "　　1. 실재, 의식 및 종교 비교"]:
        content = load_section("03-1_분포와_특징.md")
        render_section(content, COMPONENTS_03_1)

    if selection in ["Ⅲ. 취사선택 양상과 특징", "　　2. 보편화하기와 비교하기"]:
        content = load_section("03-2_보편화와_비교.md")
        render_section(content, COMPONENTS_03_2)


# =============================================================================
# Ⅳ. 철학 개념을 다루는 방식
# =============================================================================

elif selection in ["Ⅳ. 철학 개념을 다루는 방식", "　　1. 철학적이지만 '철학'은 회피", "　　2. 哲理로서의 인내천"]:
    st.header("Ⅳ. 철학 개념을 다루는 방식")

    if selection in ["Ⅳ. 철학 개념을 다루는 방식", "　　1. 철학적이지만 '철학'은 회피"]:
        content = load_section("04-1_철학_기표_소거.md")
        render_section(content, COMPONENTS_04_1)

    if selection in ["Ⅳ. 철학 개념을 다루는 방식", "　　2. 哲理로서의 인내천"]:
        content = load_section("04-2_철리_인내천.md")
        render_section(content, COMPONENTS_04_2)


# =============================================================================
# Ⅴ. 맺음말
# =============================================================================

elif selection == "Ⅴ. 맺음말":
    content = load_section("05_맺음말.md")
    render_section(content, {})


# =============================================================================
# 부록
# =============================================================================

elif selection == "부록":
    st.header("부록")
    content = load_section("06_부록.md")
    render_section(content, COMPONENTS_06)


# =============================================================================
# 푸터
# =============================================================================

st.markdown("---")
st.caption("© 2026 허수 | Powered by Streamlit | 발표문 상태라 외부 인용은 삼가해 주세요")
