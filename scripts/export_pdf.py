"""
Streamlit 웹앱 → PDF 변환 스크립트 (Playwright)

사용법:
    pip install playwright
    playwright install chromium
    python scripts/export_pdf.py

네트워크 그래프(iframe)는 스크린샷으로 캡처하여 이미지로 대체합니다.
"""

import asyncio
import base64
import os
import subprocess
import sys
import time

from playwright.async_api import async_playwright

# ============================================================
# 설정 — 필요에 따라 수정하세요
# ============================================================

STREAMLIT_PORT = 8502
LOCAL_URL = f"http://localhost:{STREAMLIT_PORT}"

# PDF 상단에 표시할 Streamlit Cloud URL
WEB_URL = "https://phenomenal-realism-kr-8gr9edsgfre4exrwnbbqrq.streamlit.app/"

# 출력 파일
OUTPUT_PDF = "발표문.pdf"

# 뷰포트 너비 (px)
VIEWPORT_WIDTH = 1200


# ============================================================
# 메인 함수
# ============================================================

async def main():
    project_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
    app_path = os.path.join(project_root, "app", "app.py")
    output_path = os.path.join(project_root, OUTPUT_PDF)

    # ── 1. Streamlit 서버 시작 ──────────────────────────────
    print("[1/7] Streamlit 서버 시작...")
    server = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run", app_path,
            "--server.port", str(STREAMLIT_PORT),
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false",
        ],
        cwd=project_root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(8)

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(
                viewport={"width": VIEWPORT_WIDTH, "height": 900},
                device_scale_factor=2,  # 고해상도 캡처
            )

            # ── 2. 페이지 로드 ──────────────────────────────
            print("[2/7] 페이지 로드...")
            await page.goto(LOCAL_URL, wait_until="networkidle", timeout=90_000)
            await page.wait_for_timeout(3000)

            # ── 3. 전체 스크롤 → lazy 콘텐츠 로드 ───────────
            print("[3/7] 전체 콘텐츠 로드 (스크롤)...")
            await page.evaluate("""
                async () => {
                    const delay = ms => new Promise(r => setTimeout(r, ms));
                    const scroller =
                        document.querySelector('section.main') ||
                        document.querySelector('[data-testid="stAppViewContainer"]') ||
                        document.documentElement;
                    const h = scroller.scrollHeight;
                    for (let y = 0; y < h; y += 400) {
                        scroller.scrollTop = y;
                        window.scrollTo(0, y);
                        await delay(250);
                    }
                    scroller.scrollTop = 0;
                    window.scrollTo(0, 0);
                    await delay(1500);
                }
            """)
            await page.wait_for_timeout(5000)

            # ── 4. 사이드바·UI 제거 (iframe 캡처 전에 실행) ──
            print("[4/7] UI 요소 제거...")
            await page.evaluate("""
                () => {
                    const hide = sel => {
                        const el = document.querySelector(sel);
                        if (el) el.style.display = 'none';
                    };
                    hide('[data-testid="stSidebar"]');
                    hide('[data-testid="collapsedControl"]');
                    hide('[data-testid="stToolbar"]');
                    hide('[data-testid="stDecoration"]');
                    hide('footer');
                    hide('#MainMenu');
                    hide('header[data-testid="stHeader"]');

                    const appView = document.querySelector(
                        '[data-testid="stAppViewContainer"]'
                    );
                    if (appView) appView.style.marginLeft = '0';
                }
            """)
            # 사이드바 제거 후 레이아웃 리플로우 대기
            await page.wait_for_timeout(2000)

            # ── 5. 네트워크 그래프 리사이즈 → iframe 캡처 ────
            print("[5/7] 네트워크 그래프 리사이즈 + 캡처...")

            # (5a) 프레임 내부 Plotly 그래프 축소 + 범례 표시
            GRAPH_H = 700
            for frame in page.frames:
                if frame == page.main_frame:
                    continue
                try:
                    has_plotly = await frame.evaluate(
                        "typeof Plotly !== 'undefined'"
                    )
                    if not has_plotly:
                        continue
                    await frame.evaluate(f"""
                        () => {{
                            const gd = document.querySelector('.js-plotly-plot')
                                    || document.querySelector('.plotly-graph-div');
                            if (!gd || !window.Plotly) return;
                            Plotly.relayout(gd, {{
                                height: {GRAPH_H},
                                showlegend: true,
                                legend: {{
                                    orientation: 'h',
                                    x: 0.5, y: -0.02,
                                    xanchor: 'center',
                                    yanchor: 'top',
                                    bgcolor: 'rgba(255,255,255,0.9)',
                                    bordercolor: '#ccc',
                                    borderwidth: 1,
                                    font: {{ size: 10 }}
                                }},
                                margin: {{ l: 5, r: 5, t: 30, b: 80 }}
                            }});
                        }}
                    """)
                    print(f"   → Plotly 그래프 리사이즈: {GRAPH_H}px")
                    await page.wait_for_timeout(2000)
                except Exception:
                    pass

            # (5b) iframe 요소 높이도 맞추고 스크린샷
            iframes = await page.query_selector_all("iframe")
            replaced = 0
            for idx, iframe_el in enumerate(iframes):
                try:
                    visible = await iframe_el.is_visible()
                    if not visible:
                        continue
                    box = await iframe_el.bounding_box()
                    if not box or box["height"] < 50:
                        continue

                    # iframe 높이를 그래프 크기에 맞춤
                    await iframe_el.evaluate(
                        f"el => {{ el.style.height = '{GRAPH_H + 10}px'; }}"
                    )
                    await page.wait_for_timeout(500)

                    # iframe 스크린샷
                    shot = await iframe_el.screenshot(type="png")
                    b64 = base64.b64encode(shot).decode()

                    # iframe의 최상위 컨테이너를 통째로 제거하고
                    # 그 자리에 이미지를 직접 삽입
                    await iframe_el.evaluate(
                        """(el, src) => {
                            // element-container 찾기 (Streamlit 래퍼)
                            let container = el;
                            while (container.parentElement) {
                                const tid = container.parentElement
                                    .getAttribute('data-testid');
                                if (tid === 'stVerticalBlock' ||
                                    tid === 'stMainBlockContainer') break;
                                container = container.parentElement;
                            }
                            const img = document.createElement('img');
                            img.src = src;
                            img.style.width = '100%';
                            img.style.display = 'block';
                            img.style.margin = '0';
                            // 컨테이너를 이미지로 교체
                            container.parentNode.replaceChild(img, container);
                        }""",
                        f"data:image/png;base64,{b64}",
                    )
                    replaced += 1
                    w = int(box["width"])
                    print(f"   → iframe #{idx} 캡처 완료 ({w}x{GRAPH_H}px)")
                except Exception as e:
                    print(f"   → iframe #{idx} 건너뜀: {e}")

            if replaced == 0:
                print("   → 대체할 iframe 없음")

            # ── 6. PDF 레이아웃 최종 조정 ────────────────────
            print("[6/7] PDF 레이아웃 조정...")
            await page.evaluate(
                """(webUrl) => {

                    // =============================================
                    // (A) CSS 주입
                    // =============================================
                    const s = document.createElement('style');
                    s.textContent = `
                        /* ── 본문 글자 크기 13pt ── */
                        [data-testid="stMainBlockContainer"] p,
                        [data-testid="stMainBlockContainer"] li,
                        [data-testid="stMainBlockContainer"] span,
                        [data-testid="stMainBlockContainer"] div.stMarkdown {
                            font-size: 13pt !important;
                            line-height: 1.7 !important;
                        }
                        /* 표: 11pt + 행간 촘촘하게 */
                        [data-testid="stMainBlockContainer"] td,
                        [data-testid="stMainBlockContainer"] th {
                            font-size: 11pt !important;
                            padding: 2px 5px !important;
                            line-height: 1.2 !important;
                        }
                        /* 표 7(chapter_dist) 등 단순 표: 더 납작하게 */
                        .pdf-compact-table td,
                        .pdf-compact-table th {
                            padding: 1px 5px !important;
                            font-size: 10pt !important;
                            line-height: 1.15 !important;
                        }
                        /* 캡션 */
                        [data-testid="stMainBlockContainer"] .stCaption,
                        [data-testid="stMainBlockContainer"] caption {
                            font-size: 10pt !important;
                        }
                        /* ── 인쇄 색상 유지 ── */
                        @media print {
                            * {
                                -webkit-print-color-adjust: exact !important;
                                color-adjust: exact !important;
                            }
                        }
                        /* ── 페이지 나눔 제어 ── */
                        /* 헤딩 뒤 끊김 방지 (표 제목 텍스트가 다음 페이지로 넘어가지 않도록) */
                        h1, h2, h3, h4 {
                            page-break-after: avoid !important;
                            break-after: avoid !important;
                        }
                        /* 표는 페이지 걸쳐도 OK (항목 9) */
                        /* 이미지는 내부 끊김 방지 */
                        img {
                            page-break-inside: avoid !important;
                            break-inside: avoid !important;
                        }
                        /* ── Streamlit 기본 간격 축소 ── */
                        [data-testid="stVerticalBlock"] {
                            gap: 0.4rem !important;
                        }
                        /* st.header() 하단 여백 제거 (항목 3) */
                        [data-testid="stHeading"] {
                            margin-bottom: 0 !important;
                            padding-bottom: 0 !important;
                        }
                        [data-testid="stHeading"] h2,
                        [data-testid="stHeading"] h3 {
                            margin-bottom: 0.1rem !important;
                            padding-bottom: 0 !important;
                        }
                        /* 표 제목 단락이 페이지 끝에 홀로 남지 않도록 */
                        .pdf-title-before-table {
                            page-break-after: avoid !important;
                            break-after: avoid !important;
                        }
                    `;
                    document.head.appendChild(s);

                    // =============================================
                    // (B) 메인 제목 영역 간격 최소화
                    // =============================================
                    const allH2 = document.querySelectorAll('h2');
                    for (const h2 of allH2) {
                        if (h2.textContent.includes('현상즉실재론')) {
                            h2.style.fontSize = '25px';
                            h2.style.wordBreak = 'keep-all';
                            h2.style.marginTop = '0';
                            h2.style.marginBottom = '0';
                            h2.style.paddingTop = '0';
                            h2.style.paddingBottom = '0';
                            h2.style.lineHeight = '1.1';
                            h2.style.marginBottom = '-2px';
                            // 부제: 거의 붙이기
                            const subtitle =
                                h2.parentElement.querySelector('h3');
                            if (subtitle) {
                                subtitle.style.marginTop = '0';
                                subtitle.style.marginBottom = '0';
                                subtitle.style.paddingTop = '0';
                                subtitle.style.paddingBottom = '0';
                                subtitle.style.lineHeight = '1.1';
                            }
                            // 발표자 아래 가로줄(hr) 삭제
                            const mdContainer = h2.closest(
                                '[data-testid="stMarkdownContainer"]'
                            ) || h2.closest('div');
                            const hrs = mdContainer.querySelectorAll('hr');
                            hrs.forEach(hr => hr.style.display = 'none');
                            // 발표자: 한 줄만 띄우기
                            const authorDiv = h2.closest('div[style]')
                                ?.nextElementSibling;
                            if (authorDiv) {
                                const authorP = authorDiv.querySelector('p');
                                if (authorP) {
                                    authorP.style.marginTop = '4px';
                                    authorP.style.marginBottom = '0';
                                    authorP.style.fontSize = '15px';
                                }
                            }
                            break;
                        }
                    }

                    // =============================================
                    // (C) 표/그림 제목 단락에 break-after: avoid 부여
                    //     (표가 페이지 걸쳐도 OK, 제목만 떨어지지 않게)
                    // =============================================
                    const mdEls = document.querySelectorAll(
                        '[data-testid="stMarkdownContainer"]'
                    );
                    mdEls.forEach(md => {
                        const text = md.textContent || '';
                        if (/[<＜](?:표|그림)\s*\d/.test(text) ||
                            /^(?:표|그림)\s*\d/.test(text.trim())) {
                            // 이 요소의 최상위 element-container 에 클래스 부여
                            const ec = md.closest(
                                '[data-testid="element-container"]'
                            );
                            if (ec) ec.classList.add('pdf-title-before-table');
                        }
                    });

                    // =============================================
                    // (D) 표 스타일: 헤더 가운데정렬 + 특정 표 납작하게
                    // =============================================
                    const allTables = document.querySelectorAll('table');
                    allTables.forEach(tbl => {
                        const ths = tbl.querySelectorAll('th');

                        // 모든 표 헤더 가운데 정렬
                        ths.forEach(th => {
                            th.style.textAlign = 'center';
                        });

                        // 표 6: "유사도 구간" 열 — 수치 열 가운데 정렬
                        const isTable6 = Array.from(ths).some(
                            th => th.textContent.includes('유사도 구간')
                        );
                        if (isTable6) {
                            ths.forEach(th => {
                                th.style.whiteSpace = 'nowrap';
                            });
                            tbl.querySelectorAll('td').forEach((td, i) => {
                                const col = i % ths.length;
                                if (col <= 2) td.style.textAlign = 'center';
                            });
                        }

                        // 표 7: "1924 장" + "제목" 열 — 납작하게
                        const isTable7 = Array.from(ths).some(
                            th => th.textContent.trim() === '1924 장'
                        );
                        // 표 8: "1915 장" + "1924 장" 열
                        const isTable8 = Array.from(ths).some(
                            th => th.textContent.trim() === '1915 장'
                        );
                        if (isTable7 || isTable8) {
                            tbl.classList.add('pdf-compact-table');
                        }
                    });

                    // =============================================
                    // (D2) 히트맵 이미지 높이 제한 (표7+히트맵 같은 페이지)
                    // =============================================
                    const stImages = document.querySelectorAll(
                        '[data-testid="stImage"] img'
                    );
                    stImages.forEach(img => {
                        // 히트맵 캡션으로 식별
                        const cap = img.closest('[data-testid="stImage"]')
                            ?.querySelector('[data-testid="stCaption"]');
                        const capText = cap?.textContent || '';
                        if (capText.includes('유효 참조쌍') ||
                            capText.includes('히트맵') ||
                            capText.includes('색상은 참조쌍 개수')) {
                            img.style.maxHeight = '300px';
                            img.style.width = 'auto';
                            img.style.margin = '0 auto';
                            img.style.display = 'block';
                        }
                    });

                    // =============================================
                    // (E) iframe 교체 후 남은 고정 높이 전부 제거
                    // =============================================
                    // 방법: 페이지 내 높이 > 800px인 div를 모두 찾아 auto로
                    document.querySelectorAll('div').forEach(div => {
                        const h = div.style.height;
                        if (h && parseInt(h) > 800) {
                            div.style.height = 'auto';
                        }
                    });
                    // stCustomComponentV1 래퍼 직접 타겟
                    document.querySelectorAll(
                        '[data-testid="stCustomComponentV1"]'
                    ).forEach(el => {
                        el.style.height = 'auto';
                        el.style.minHeight = '0';
                    });
                    // 교체된 이미지 부모 여백도 제거
                    document.querySelectorAll('img[src^="data:image"]')
                        .forEach(img => {
                            img.style.marginBottom = '0';
                            let p = img.parentElement;
                            for (let i = 0; i < 10 && p; i++) {
                                p.style.height = 'auto';
                                p.style.minHeight = '0';
                                p.style.overflow = 'visible';
                                p.style.marginBottom = '0';
                                p.style.paddingBottom = '0';
                                p = p.parentElement;
                            }
                        });

                    // =============================================
                    // (F) 본문 시작 직전에 웹 URL 삽입
                    // =============================================
                    const container =
                        document.querySelector(
                            '[data-testid="stMainBlockContainer"]'
                        ) || document.querySelector('.block-container');
                    if (container && webUrl) {
                        const d = document.createElement('div');
                        d.style.cssText =
                            'text-align:center; padding:4px 0 6px; '
                            + 'color:#666; font-size:11px; '
                            + 'border-bottom:1px solid #ccc; '
                            + 'margin-bottom:4px;';
                        d.innerHTML =
                            '※ 본 발표문의 인터랙티브 웹 버전: '
                            + '<a href="' + webUrl + '" '
                            + 'style="color:#0068c9;">'
                            + webUrl + '</a>';
                        container.insertBefore(d, container.firstChild);
                    }

                    // =============================================
                    // (G) Ⅰ.머리말 바로 위에 2단 목차 삽입
                    // =============================================
                    const h2s = document.querySelectorAll('h2');
                    for (const h2 of h2s) {
                        const t = h2.textContent.trim();
                        if (/^Ⅰ/.test(t) && t.includes('머리말')) {
                            const toc = document.createElement('div');
                            toc.style.cssText =
                                'margin:12px 0 8px; padding:10px 16px; '
                                + 'border:1px solid #bbb; '
                                + 'page-break-inside:avoid;';
                            toc.innerHTML = `
<div style="display:flex; gap:24px; font-size:11pt; line-height:1.7;">
  <div style="flex:1;">
    <div style="font-weight:bold;">Ⅰ. 머리말</div>
    <div style="font-weight:bold; margin-top:4px;">Ⅱ. DB 구축과 다국어 비교 방법</div>
    <div style="padding-left:16px; font-size:10pt;">1. 문단별 데이터를 비교 단위로</div>
    <div style="padding-left:16px; font-size:10pt;">2. 공통 한자어 비율을 계산</div>
    <div style="font-weight:bold; margin-top:4px;">Ⅲ. 취사선택 양상과 특징</div>
    <div style="padding-left:16px; font-size:10pt;">1. 참조쌍의 분포: 두 장에 97%가 집중</div>
    <div style="padding-left:16px; font-size:10pt;">2. 가져온 것과 버린 것</div>
  </div>
  <div style="flex:1;">
    <div style="visibility:hidden;">Ⅰ. 머리말</div>
    <div style="font-weight:bold; margin-top:4px;">Ⅳ. 철학 개념을 다루는 방식</div>
    <div style="padding-left:16px; font-size:10pt;">1. '철학'이라는 이름 지우기</div>
    <div style="padding-left:16px; font-size:10pt;">2. 원문에서 읽는 대체 패턴</div>
    <div style="padding-left:16px; font-size:10pt;">3. 패턴의 검증</div>
    <div style="font-weight:bold; margin-top:4px;">Ⅴ. 맺음말</div>
    <div style="margin-top:4px;">부록</div>
  </div>
</div>`;
                            h2.parentElement.insertBefore(toc, h2);
                            break;
                        }
                    }
                }""",
                WEB_URL,
            )
            await page.wait_for_timeout(500)

            # ── 7. PDF 생성 (페이지 번호 포함) ────────────────
            print(f"[7/7] PDF 생성: {output_path}")

            footer_html = """
                <div style="
                    font-size: 18px;
                    color: #888;
                    width: 100%;
                    text-align: right;
                    padding-right: 15mm;
                ">
                    <span class="pageNumber"></span>/<span class="totalPages"></span>
                </div>
            """

            await page.pdf(
                path=output_path,
                format="A4",
                print_background=True,
                margin={
                    "top": "12mm",
                    "bottom": "16mm",
                    "left": "15mm",
                    "right": "15mm",
                },
                display_header_footer=True,
                header_template='<span></span>',
                footer_template=footer_html,
            )

            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"\n완료! '{OUTPUT_PDF}' ({size_mb:.1f} MB)")

            await browser.close()
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
        print("Streamlit 서버 종료.")


if __name__ == "__main__":
    asyncio.run(main())
