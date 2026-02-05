# CLAUDE.md

## Project Overview

디지털 문헌학 연구: 이노우에 데츠지로 『철학과 종교』(1915) × 이돈화 『인내천요의』(1924) 텍스트 관계 분석. 서울대 국사학과 허수 교수 연구 프로젝트.

## Commands

```bash
pip install -r app/requirements.txt   # 의존성 설치
streamlit run app/app.py              # 발표용 웹앱 실행
```

## Architecture

```
phenomenal-realism-kr/
├── app/
│   ├── app.py                  # Streamlit 발표용 웹앱 (렌더링 엔진 + 컴포넌트 함수)
│   ├── sections/               # 발표문 텍스트 (마크다운, <!-- component: name --> 마커 포함)
│   └── requirements.txt
├── data/
│   ├── corpus/                 # 코퍼스 원본 DB (1벌)
│   │   ├── BK_IT_1915_PR_v1.3.xlsx   # 철학과 종교 (11,088행)
│   │   ├── BK_IT_1915_PR.txt
│   │   ├── BK_YD_1924_IY_v1.2.xlsx   # 인내천요의 (2,254행)
│   │   └── BK_YD_1924_IY.txt
│   └── analysis/               # 유사도 분석 결과 (CSV, JSON)
├── docs/                       # 연구 문서, 분석 노트, 보고서
├── images/                     # 앱 사용 이미지
├── scripts/                    # 분석 스크립트
├── 삭제검토대상/                 # 삭제 검토 중인 파일
├── CLAUDE.md
└── README.md
```

### Data Structure

- 1915: `C##-P##-S##` (장-문단-문장), C00~C28 (29개 장: 서장 1 + 본문 26 + 부록 2)
- 1924: `C##-S##-I##-P##-S##` (장-절-항-문단-문장), C01~C06 (6개 장)

## Coding Guidelines

1. **역할**: 역사학적 맥락을 이해하는 연구 조교
2. **언어**: 한국어, 정중하고 학술적인 어조
3. **기술**: Python 3.11, Streamlit, Pandas, Plotly
4. **원칙**: 사료 원문 변형 최소화

## Research Context

**분석의 3대 축**:
1. 지식의 차용: 과학적 권위의 투명한 수용
2. 논리의 내재화: '철학' 개념의 소거와 주체 교체
3. 가치의 전복: 제국주의 논리의 해체와 재구성

**분석 방법**: 한자어 토큰화 (`r'[一-龥]{2,}'`), Jaccard 유사도, 문단 단위 비교

### 빈도 카운트 기준

- **포함**: `line_class`가 `TEXT`, `STRUCT`인 행
- **제외**: `RTC_TEXT`, `ANNOTATION`, `structure_id`가 `TOC`/`ROOT`

## 현재 작업 상태 (2026-02-05)

### 학술대회 발표문 웹앱 업데이트 (진행 중)

**목표**: 공식 학술대회 발표를 위해 기존 웹앱(`app/app.py`) 업데이트

**완료된 작업**:
1. 현재 웹앱 스토리라인 점검 완료
2. 장절별 논지 중심 스토리라인 정리 → `docs/presentation-storyline.md` 저장
3. 폴더 구조 단순화 완료 (DB 통합, 빈 디렉토리 정리, 구버전 삭제)
4. 발표문 텍스트를 `app/sections/` 마크다운 파일로 분리 완료 (9개 .md 파일)
5. app.py를 `render_section()` + `<!-- component: name -->` 마커 기반 구조로 리팩터링 완료
6. 테이블 데이터를 `app/tables.json`으로 분리 완료 (18개 테이블)
7. 미사용 파일 `삭제검토대상/`으로 이동 완료
8. 웹앱 레이아웃 변경 완료: 사이드바 라디오 버튼 → HTML 앵커 목차, 본문 한 페이지 스크롤 방식으로 전환, 사이드바 너비 240px 축소
9. 스토리라인 논리 검토 및 수정 완료:
   - 팩트 오류 수정: 1924 문단 수 366→365 (전체 문서 8곳)
   - C03-S04 참조쌍 수 재검증 완료 (발표문 수치 정확 확인)
   - Ⅲ→Ⅳ 전환 동기 부여 문장 추가 ('모듈' → '기표 소거' 연결)
   - Ⅳ-1 역상관 주장 보강: 반론 선제 제시 + 대조군(내용어 vs 범주어) 추가
   - Ⅳ-2 대체 패턴 사례 수(4건) 한계 명시, 인과적 어조 완화

**다음 작업**:
- 스토리라인 기반으로 웹앱 내용 추가 수정/보완 검토

**참고 파일**:
- `app/app.py`: 발표용 웹앱 (한 페이지 스크롤 + 사이드바 앵커 목차)
- `app/sections/`: 발표문 텍스트 마크다운 (9개 파일, `<!-- component: name -->` 마커 포함)
- `app/tables.json`: 테이블 데이터 (18개 테이블)
- `docs/presentation-storyline.md`: 장절별 스토리라인 정리

---

### 이전 작업 (2026-01-24)

**통합 보고서 완성**: 3장6절 체제 논문/발표용 보고서 (`integrated-analysis-report.md`) 작성 완료.

문단 유사도 재산출 완료 (626 × 365 = 228,490개 쌍, 임계값 0.1). **최종 검증 완료: 135개 → 111개 유효 쌍** (24개 노이즈 제외).

### 참조쌍 노이즈 필터링 (2026-01-24 확정)

**제외 기준**:
1. **서수만 공유** (7개): 第一, 第二 등만 일치
2. **범용어만 공유** (17개): 如何, 對照, 區別, 差異點, 宇宙(단독), 世界(단독) 등

**포함 확정** (검토 후 유효 판정):
- Rank 6, 55, 113, 45: 超人的, 勢力, 一神敎 (종교학 핵심 용어)
- Rank 26: 人類, 不調和 (메치니코프 진화론 맥락)

**최종 통계**:
- 총 검토: 135개 (유사도 ≥ 0.1)
- 유효: **111개**
- 제외: 24개 (서수 7개 + 범용어 17개)

**유효 쌍 분포 (1924 장별)**:
- C01 緖言: 3개
- C03 人乃天과 眞理: 45개
- C06 人乃天에 對한 雜感: 63개

## 종합 분석 보고서

### 통합 보고서 (논문/발표용)

**`docs/analysis-reports/integrated-analysis-report.md`** — 「디지털문헌학으로 본 20세기 초 현상즉실재론의 한국 유입: 『철학과 종교』에 대한 이돈화의 취사선택을 중심으로」

| 장 | 절 | 내용 |
|---|---|------|
| Ⅰ | 머리말 | 연구 배경, 선행연구(허수 2011, 2015), 연구 질문 |
| Ⅱ | 연구 설계 | 2.1 코퍼스 구축, 2.2 분석 방법론 (자카드 유사도) |
| Ⅲ | 참조쌍 분석 | 3.1 분포 분석, 3.2 핵심 구간 분석 (C03-S04, C06-S06) |
| Ⅳ | 차용의 양상과 해석 | 4.1 지식의 차용, 4.2 '哲學' 기표의 소거 |
| Ⅴ | 맺음말 | 결론 및 한계 |

### 상세 분석 보고서

**`docs/analysis-reports/paragraph-similarity-analysis-report.md`** — 8장 체제 상세 분석 보고서

| 장 | 내용 |
|---|------|
| 제1장 | 연구 배경과 목적 |
| 제2장 | 연구 방법론 (코퍼스 구축, 한자어 자카드 유사도) |
| 제3장 | 유사도 분포와 임계값 0.1 설정의 타당성 |
| 제4장 | 노이즈 필터링 (135개 → 111개) |
| 제5장 | 장-장 단위 분포 분석 (히트맵) |
| 제6장 | 핵심 구간 상세 분석 (C03-S04, C06-S06) |
| 제7장 | 종합 해석 ('이데올로기적 모듈'로서의 차용) |
| 제8장 | 결론 및 한계 |
| 부록 | 데이터 파일 목록, 상위 20개 참조쌍, 관련 문서 목록 |

## 상세 문서

| 문서 | 내용 |
|------|------|
| `docs/db_structure.md` | DB 구조 및 버전 이력 |
| `docs/research-log/2025-01-23-철학빈도분석.md` | '哲學' 빈도 분석 기록 |
| `docs/research-log/2025-01-23-허수논문반영.md` | 허수(2025) 논문 반영 작업 |
| `docs/analysis-notes/paragraph-similarity.md` | 문단 유사도 분석 방법론 및 결과 |
| `docs/analysis-notes/chapter-heatmap.md` | 장-장 히트맵 분석, **방법론 요약 포함** |
| `docs/analysis-notes/chapter-pairs-detail.md` | 주요 장-장 조합 상세 분석 |
| `docs/analysis-notes/c03s04-reference-analysis.md` | **C03-S04 항별 참조 분석** (52개 쌍) |
| `docs/analysis-notes/i02-realite-flow-analysis.md` | **I02 實在와 人乃天 논리 흐름 분석** |
| `docs/analysis-notes/i05-consciousness-flow-analysis.md` | **I05 意識과 人乃天 논리 흐름 분석** |
| `docs/analysis-notes/c06-reference-analysis.md` | **C06 人乃天에 對한 雜感 참조 분석** (70개 쌍, S06 집중) |
| `docs/analysis-notes/c13-c06-reference-analysis.md` | **C13×C06 儒基 비교 프레임워크 차용** (31개 쌍) |
| `docs/analysis-notes/c14-c06-reference-analysis.md` | **C14×C06 佛基 비교 프레임워크 차용** (20개 쌍) |
| `docs/analysis-notes/validated-pairs-filtering.md` | **참조쌍 노이즈 필터링 검증** (135→111개) |
| `docs/analysis-reports/chapter8-philosophy-signifier-analysis.md` | **'哲學' 기표 소거 분석** (대체어 패턴 3종) |

## 데이터 파일

| 파일 | 내용 |
|------|------|
| `data/corpus/BK_IT_1915_PR_v1.3.xlsx` | 철학과 종교 코퍼스 DB (11,088행) |
| `data/corpus/BK_YD_1924_IY_v1.2.xlsx` | 인내천요의 코퍼스 DB (2,254행) |
| `data/analysis/validated_pairs_final.csv` | **최종 검증된 참조쌍** (111개, 노이즈 24개 제외) |
| `docs/analysis-reports/paragraph-similarity-data.xlsx` | **종합 보고서 데이터** (6개 시트: 요약통계, 장별분포, 주요조합, C03/C06 참조쌍, 전체 111개) |
