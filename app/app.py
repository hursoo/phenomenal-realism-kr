import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import re
import json


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


TABLES_PATH = os.path.join(os.path.dirname(__file__), "tables.json")


@st.cache_data
def load_tables() -> dict:
    """tables.json에서 테이블 데이터를 캐싱하여 로드합니다."""
    with open(TABLES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def render_table(key: str):
    """tables.json의 키를 기준으로 테이블을 렌더링합니다."""
    tables = load_tables()
    entry = tables[key]
    st.table(pd.DataFrame(entry["data"]))
    if "caption" in entry:
        st.caption(entry["caption"])


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
    render_table("corpus_table")


def render_paragraph_table():
    render_table("paragraph_table")


# --- Ⅱ-2. 공통 한자어 비율 ---

def render_stats_table():
    render_table("stats_table")


def render_common_tokens_table():
    render_table("common_tokens_table")


def render_range_example_table():
    render_table("range_example_table")


def render_valid_pairs_table():
    render_table("valid_pairs_table")


# --- Ⅲ-1. 분포와 특징 ---

def render_chapter_dist_table():
    render_table("chapter_dist_table")


def render_chapter_dist_chart():
    fig = create_chapter_distribution_chart()
    st.plotly_chart(fig, use_container_width=True)


def render_heatmap():
    col1, col2, col3 = st.columns([1, 6, 1])
    with col2:
        heatmap_path = os.path.join(os.path.dirname(__file__), "..", "images", "chapter_heatmap_avg_above_threshold.png")
        if os.path.exists(heatmap_path):
            st.image(heatmap_path, caption="111개 유효 참조쌍 (자카드 유사도 ≥ 0.1). 색상은 참조쌍 개수, 괄호 안은 평균 유사도.")
        else:
            alt_path = os.path.join(os.path.dirname(__file__), "..", "images", "chapter_heatmap_avg_above_threshold.png")
            if os.path.exists(alt_path):
                st.image(alt_path, caption="장-장 단위 유효 참조쌍 분포")
            else:
                st.info("히트맵 이미지 파일을 찾을 수 없습니다.")


def render_network_graph():
    network_path = os.path.join(os.path.dirname(__file__), "..", "images", "reference_pairs_network.html")
    if os.path.exists(network_path):
        with open(network_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        import streamlit.components.v1 as components
        components.html(html_content, height=1400, scrolling=True)
    else:
        st.info("네트워크 그래프 파일을 찾을 수 없습니다.")


def render_ref_table():
    render_table("ref_table")


def render_c03s04_table():
    render_table("c03s04_table")


def render_c06s06_table():
    render_table("c06s06_table")


# --- Ⅲ-2. 보편화와 비교 ---

def render_borrow_table():
    render_table("borrow_table")


def render_invert_table():
    render_table("invert_table")


# --- Ⅳ-1. 철학 기표 소거 ---

def render_phil_freq_table():
    render_table("phil_freq_table")


def render_rank_chart():
    fig = create_philosophy_rank_chart()
    st.plotly_chart(fig, use_container_width=True)


def render_freq_compare_table():
    render_table("freq_compare_table")


def render_inverse_table():
    render_table("inverse_table")


def render_paradox_image():
    col1, col2, col3 = st.columns([1, 6, 1])
    with col2:
        paradox_path = os.path.join(os.path.dirname(__file__), "..", "images", "c03s04_philosophy_paradox.png")
        if os.path.exists(paradox_path):
            st.image(paradox_path, caption="C03-S04 항별 참조쌍 개수(막대)와 '哲學' 출현 빈도(선). 참조 밀도가 높은 I02, I05에서 '哲學'은 0회.")
        else:
            alt_path = os.path.join(os.path.dirname(__file__), "..", "images", "c03s04_philosophy_paradox.png")
            if os.path.exists(alt_path):
                st.image(alt_path, caption="C03-S04 항별 참조쌍 개수와 '哲學' 출현 빈도의 역상관")


# --- Ⅳ-2. 철리 인내천 ---

def render_diff_vocab_table():
    render_table("diff_vocab_table")


def render_phil_compound_table():
    render_table("phil_compound_table")


def render_sub_stats_table():
    render_table("sub_stats_table")


def render_pattern_table():
    render_table("pattern_table")


# --- 부록 ---

def render_file_table():
    render_table("file_table")


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
        render_table("pairs_fallback_table")


# =============================================================================
# 페이지 기본 설정
# =============================================================================

st.set_page_config(
    page_title="디지털 문헌학: 현상즉실재론의 유입",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 스타일 설정
st.markdown("""
    <style>
    /* 다운로드 툴바 숨기기 */
    [data-testid="stElementToolbar"] { display: none; }

    /* 사이드바 너비 축소 */
    [data-testid="stSidebar"] { min-width: 240px; max-width: 240px; }

    /* 사이드바 목차 */
    .toc a {
        display: block;
        padding: 3px 0;
        color: inherit;
        text-decoration: none;
        font-size: 13px;
    }
    .toc a:hover { color: #ff4b4b; }
    .toc a.sub { padding-left: 12px; font-size: 12px; }
    </style>
    """, unsafe_allow_html=True)


# =============================================================================
# 사이드바 목차
# =============================================================================

st.sidebar.title("목차")
st.sidebar.markdown("""
<div class="toc">
<a href="#sec-1" target="_self">Ⅰ. 머리말</a>
<a href="#sec-2" target="_self">Ⅱ. DB 구축과 다국어 비교 방법</a>
<a class="sub" href="#sec-2-1" target="_self">1. 문단별 데이터를 비교 단위로</a>
<a class="sub" href="#sec-2-2" target="_self">2. 공통 한자어 비율을 계산</a>
<a href="#sec-3" target="_self">Ⅲ. 취사선택 양상과 특징</a>
<a class="sub" href="#sec-3-1" target="_self">1. 참조쌍의 분포: 두 장에 97%가 집중</a>
<a class="sub" href="#sec-3-2" target="_self">2. 가져온 것과 버린 것</a>
<a href="#sec-4" target="_self">Ⅳ. 철학 개념을 다루는 방식</a>
<a class="sub" href="#sec-4-1" target="_self">1. '철학'이라는 이름 지우기</a>
<a class="sub" href="#sec-4-2" target="_self">2. 원문에서 읽는 대체 패턴</a>
<a class="sub" href="#sec-4-3" target="_self">3. 패턴의 검증</a>
<a href="#sec-5" target="_self">Ⅴ. 맺음말</a>
<a href="#sec-6" target="_self">부록</a>
</div>
""", unsafe_allow_html=True)


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
    "range_example_table": render_range_example_table,
    "valid_pairs_table": render_valid_pairs_table,
}

COMPONENTS_03_1 = {
    "chapter_dist_table": render_chapter_dist_table,
    "heatmap": render_heatmap,
    "network_graph": render_network_graph,
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
    "freq_compare_table": render_freq_compare_table,
    "inverse_table": render_inverse_table,
}

COMPONENTS_04_2 = {
    "sub_stats_table": render_sub_stats_table,
    "pattern_table": render_pattern_table,
}

COMPONENTS_04_3 = {
    "diff_vocab_table": render_diff_vocab_table,
    "phil_compound_table": render_phil_compound_table,
}

COMPONENTS_06 = {
    "file_table": render_file_table,
    "pairs_data": render_pairs_data,
}


# =============================================================================
# Ⅰ. 머리말
# =============================================================================

st.markdown('<div id="sec-1"></div>', unsafe_allow_html=True)
render_section(load_section("01_머리말.md"), {})


# =============================================================================
# Ⅱ. DB 구축과 다국어 비교 방법
# =============================================================================

st.markdown('<div id="sec-2"></div>', unsafe_allow_html=True)
st.header("Ⅱ. DB 구축과 다국어 비교 방법")

st.markdown('<div id="sec-2-1"></div>', unsafe_allow_html=True)
render_section(load_section("02-1_문단별_데이터.md"), COMPONENTS_02_1)

st.markdown('<div id="sec-2-2"></div>', unsafe_allow_html=True)
render_section(load_section("02-2_공통_한자어_비율.md"), COMPONENTS_02_2)


# =============================================================================
# Ⅲ. 취사선택 양상과 특징
# =============================================================================

st.markdown('<div id="sec-3"></div>', unsafe_allow_html=True)
st.header("Ⅲ. 취사선택 양상과 특징")

st.markdown('<div id="sec-3-1"></div>', unsafe_allow_html=True)
render_section(load_section("03-1_분포와_특징.md"), COMPONENTS_03_1)

st.markdown('<div id="sec-3-2"></div>', unsafe_allow_html=True)
render_section(load_section("03-2_보편화와_비교.md"), COMPONENTS_03_2)


# =============================================================================
# Ⅳ. 철학 개념을 다루는 방식
# =============================================================================

st.markdown('<div id="sec-4"></div>', unsafe_allow_html=True)
st.header("Ⅳ. 철학 개념을 다루는 방식")

st.markdown('<div id="sec-4-1"></div>', unsafe_allow_html=True)
render_section(load_section("04-1_철학_기표_소거.md"), COMPONENTS_04_1)

st.markdown('<div id="sec-4-2"></div>', unsafe_allow_html=True)
render_section(load_section("04-2_철리_인내천.md"), COMPONENTS_04_2)

st.markdown('<div id="sec-4-3"></div>', unsafe_allow_html=True)
render_section(load_section("04-3_패턴의_검증.md"), COMPONENTS_04_3)


# =============================================================================
# Ⅴ. 맺음말
# =============================================================================

st.markdown('<div id="sec-5"></div>', unsafe_allow_html=True)
render_section(load_section("05_맺음말.md"), {})


# =============================================================================
# 부록
# =============================================================================

st.markdown('<div id="sec-6"></div>', unsafe_allow_html=True)
st.header("부록")
render_section(load_section("06_부록.md"), COMPONENTS_06)


# =============================================================================
# 푸터
# =============================================================================

st.markdown("---")
st.caption("© 2026 허수 | Powered by Streamlit | 발표문 상태라 외부 인용은 삼가해 주세요")
