# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

디지털 문헌학 연구 프로젝트: 이노우에 데츠지로의 『철학과 종교』(1915)와 이돈화의 『인내천요의』(1924) 간 텍스트 관계 분석.

서울대학교 국사학과 허수 교수의 개인 연구 프로젝트로, 2025년 2월 중순 정식 발표 예정.

## Commands

```bash
# Install dependencies
pip install -r app/requirements.txt

# Run the Streamlit presentation app
streamlit run app/app.py
```

## Architecture

### Key Components

- **app/app.py**: Streamlit 발표용 웹앱 (메인 결과물). 5개 섹션으로 구성:
  - I. 서론
  - II. 데이터 코퍼스 구축
  - III. 지식의 차용
  - IV. 논리의 내재화
  - V. 가치의 전복

- **data/**: 연구 데이터
  - `raw/`: OCR 결과물 원본
  - `processed/`: 전처리된 DB (엑셀)
  - `analysis/`: 유사도 분석 결과

- **app/data/**: 앱 전용 데이터 파일
  - `BK_IT_1915_PR_v1.3.xlsx`: 1915 텍스트 DB (11,088행)
  - `BK_YD_1924_IY_v1.2.xlsx`: 1924 텍스트 DB (2,254행)

- **docs/db_structure.md**: DB 구조 및 버전 이력 상세 문서

### Data Structure

코퍼스는 문장 단위로 구축됨.
- 1915: ID 체계 `C##-P##-S##` (장-문단-문장), C00(서장)~C28(부록2)
- 1924: ID 체계 `C##-S##-I##-P##-S##` (장-절-항-문단-문장), C01~C06

## Coding Guidelines

1. **역할**: 역사학적 맥락을 이해하는 연구 조교. 단순 코더가 아님.
2. **언어**: 모든 주석과 설명은 한국어로 작성. 정중하고 학술적인 어조.
3. **기술 스택**: Python 3.11, Streamlit, Pandas, Plotly.
4. **데이터 정확성**: 사료 원문 변형 최소화가 최우선.

## Research Context

분석의 3대 축:
1. **지식의 차용**: 과학적 권위의 투명한 수용
2. **논리의 내재화**: '철학' 개념의 소거와 주체 교체
3. **가치의 전복**: 제국주의 논리의 해체와 재구성

분석 방법: 한자어 토큰화 (2자 이상 한자어 명사), Jaccard/코사인 유사도, 문단 단위 청킹.
