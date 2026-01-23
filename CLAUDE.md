# CLAUDE.md

## Project Overview

디지털 문헌학 연구: 이노우에 데츠지로 『철학과 종교』(1915) × 이돈화 『인내천요의』(1924) 텍스트 관계 분석. 서울대 국사학과 허수 교수 연구 프로젝트.

## Commands

```bash
pip install -r app/requirements.txt   # 의존성 설치
streamlit run app/app.py              # 발표용 웹앱 실행
```

## Architecture

- **app/app.py**: Streamlit 발표용 웹앱 (I.서론 ~ V.가치의전복)
- **app/data/**: `BK_IT_1915_PR_v1.3.xlsx` (11,088행), `BK_YD_1924_IY_v1.2.xlsx` (2,254행)
- **data/analysis/**: 유사도 분석 결과 (CSV, JSON)
- **scripts/**: 분석 스크립트
- **docs/**: 상세 문서

### Data Structure

- 1915: `C##-P##-S##` (장-문단-문장), C00~C28
- 1924: `C##-S##-I##-P##-S##` (장-절-항-문단-문장), C01~C06

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

## 현재 작업 상태 (2026-01-24)

문단 유사도 재산출 완료 (228,490개 쌍, 임계값 0.1). 장-장 히트맵 및 주요 구간 분석 진행 중.

## 상세 문서

| 문서 | 내용 |
|------|------|
| `docs/db_structure.md` | DB 구조 및 버전 이력 |
| `docs/research-log/2025-01-23-철학빈도분석.md` | '哲學' 빈도 분석 기록 |
| `docs/research-log/2025-01-23-허수논문반영.md` | 허수(2025) 논문 반영 작업 |
| `docs/analysis-notes/paragraph-similarity.md` | 문단 유사도 분석 방법론 및 결과 |
| `docs/analysis-notes/chapter-heatmap.md` | 장-장 히트맵 분석 |
| `docs/analysis-notes/chapter-pairs-detail.md` | 주요 장-장 조합 상세 분석 |
