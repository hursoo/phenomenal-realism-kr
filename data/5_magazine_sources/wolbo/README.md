# cheondogyo_wolbo_series

천도교회월보 이돈화 75편 전사 파이프라인의 본격 작업 영역. Phase 1·2·3.A·B2 완료 (2026-05-09).

## 폴더 구조

```
cheondogyo_wolbo_series/
├── README.md                     ← 본 파일
├── articles/                     ★ 본 시리즈 75편의 정착 산출물
│   └── 01_kwonyu_1911-01/        본 1편: 「勸牖天下失樂者」 (1911-01-15)
│       ├── meta.yaml             메타데이터·자르기 좌표·검증 사실
│       ├── units/                5단 이미지 (단 분리 산출, *.png는 .gitignore)
│       ├── ocr/                  도구별 raw OCR 결과 + review·decisions
│       │   ├── claude_opus_4_7/
│       │   ├── gemini/
│       │   ├── gpt5/             (참고용, 시리즈에서 제외 결정)
│       │   ├── paddle/
│       │   ├── review_*.md       단별 차이 영역 review 보고서
│       │   └── decisions_*.md    인간 중재 결정 보고서
│       └── transcripts/          ★ 최종 권위 텍스트
│           ├── article_01.high_fidelity.md     (2) 고충실 전사본 v1.1 (Soo 권위)
│           └── article_01.modern_reading.md    (3) 현대 독해본 v1.0 (Claude 띄어쓰기, Soo 검수 대기)
│
├── samples/                      옛한글·정책 측정용 부 표본
│   └── oldhangul_sample_wolbo18/  부 표본: 「新年에 對ᄒᆞᆫ 新感想으로 新發明을 公告ᄒᆞᆷ」 (1912-01-15)
│       ├── meta.yaml
│       ├── units/                정정된 자르기 (좌상·좌하 2단)
│       ├── ocr/                  3엔진 결과 + decisions
│       └── transcripts/
│
├── scripts/                      ★ 재사용 가능 스크립트
│   ├── consensus.py              ★ B2 v1: 합의 파이프라인 (analyze/all/review/draft, article-agnostic)
│   ├── add_spacing.py            ★ B2 v1: Claude API 띄어쓰기 부여 (정책 §20.b)
│   ├── article_pipeline.py       ★ B2 v1: stage 오케스트레이터 (status/next/run)
│   ├── build_series_index.py     ★ C1: 75편 시간순 정렬 + series_index 부여
│   ├── bootstrap_article.py      ★ C2.0: article 폴더 skeleton 생성 (한자 2자 slug + meta.yaml)
│   ├── transform_old_to_modern.py  (2)→(3) 변환 + 옛한글 자모 매핑 v1.0
│   ├── phase2_5_consensus.py     [legacy] article_01 전용 합의 스크립트 (consensus.py로 대체)
│   ├── phase2_1_detect_band.py   단 경계 검출 (Phase 2 시기 산출)
│   ├── phase2_3_api_probe.py     API 활성화 점검 (Phase 2 시기 산출)
│   ├── cut_article_01_units.py   본 1편 자르기 좌표 (편당 1개 스크립트)
│   ├── run_gemini_ocr.py         Gemini 2.5 Pro vision OCR (v1.1 article-agnostic)
│   ├── run_paddle_ocr.py         PaddleOCR PP-OCRv5_server (v1.1 article-agnostic)
│   └── run_gpt5_ocr.py           GPT-5 vision OCR (시리즈 제외 결정)
│
└── _archive/                     일회성·시행착오 (보존용)
    ├── probes/                   본 1편 단 분리 시 일회성 시각·column probe (.py 9개)
    ├── visual_probe/             본 1편 시각 검증 png (16개)
    └── samples_oldhangul_probes/  부 표본 시각 검증 자료 (.py 5개 + visual_probe/)
```

## 권위 기준 (2026-05-09 시점)

- **시리즈 정책 v0.3 (20 규칙)**: `../../../_design/2026-05-09_cheondogyo_wolbo_consensus_policy_v0_3.md`
- **옛한글 자모 매핑 규칙표 v1.0 (18 매핑)**: `scripts/transform_old_to_modern.py` 안 dict
- **도구 조합**: Claude Opus 4.7(주) + Gemini 2.5 Pro(보강) + PaddleOCR chinese_cht(검증). GPT-5 제외.
- **본 1편 (2)v1.1 + (3)v1.0**: `articles/01_kwonyu_1911-01/transcripts/`

## 사용법

### B2 v1 도구 (article-agnostic)

```bash
# 1. 파이프라인 상태 확인
python scripts/article_pipeline.py status --article 01_kwonyu_1911-01

# 2. 다음 자동 단계 실행 (consensus / transform / spacing 중)
python scripts/article_pipeline.py next --article 01_kwonyu_1911-01

# 3. 특정 단계만 실행
python scripts/article_pipeline.py run --article 01_kwonyu_1911-01 --stage consensus
```

### 개별 도구 직접 호출

```bash
# 합의 분석 (단별 review_*.md + (2) draft_v0 자동 초안)
python scripts/consensus.py review --article 01_kwonyu_1911-01
python scripts/consensus.py draft  --article 01_kwonyu_1911-01
python scripts/consensus.py all    --article 01_kwonyu_1911-01    # 전체 unit 요약 표
python scripts/consensus.py analyze --article 01_kwonyu_1911-01 --unit unit_3_p2u

# (2) → (3) 변환 (옛한글 자모 → 현대 자모, 한자 보존, 띄어쓰기 미부여)
python scripts/transform_old_to_modern.py \
  articles/01_kwonyu_1911-01/transcripts/article_01.high_fidelity.md \
  articles/01_kwonyu_1911-01/transcripts/article_01.modern_reading.md

# (3)에 Claude API 의미 단위 띄어쓰기 부여 (정책 §20.b 7규칙)
python scripts/add_spacing.py articles/01_kwonyu_1911-01/transcripts/article_01.modern_reading.md

# OCR 도구별 실행 (article-agnostic v1.1)
python scripts/run_gemini_ocr.py --article 01_kwonyu_1911-01
python scripts/run_gemini_ocr.py --article 01_kwonyu_1911-01 --unit unit_3_p2u --force
python scripts/run_paddle_ocr.py --article 01_kwonyu_1911-01

# 시리즈 인덱스 산출 (1회성)
python scripts/build_series_index.py

# C2 article 폴더 skeleton (한자 2자 slug + meta.yaml)
python scripts/bootstrap_article.py --series 2-9    # 범위
python scripts/bootstrap_article.py --all           # 73편 일괄 (#1·#10 제외)
python scripts/bootstrap_article.py --series 2 --dry-run  # 검토만
```

## 시리즈 인덱스 (C1 산출, 2026-05-09)

`series_index.csv` / `series_index.md`: 75편 발행일 순 1~75. 본 1편 = #1, 부 표본 = #10.

**시기 cutoff 제약**: 1911-01-15 ~ 1922-05-15 (75편). 1922-06 ~ 1924 NL 디지털 미제공으로 5건 ✗.

## 파이프라인 단계 (정책 v0.3 §3)

| 단계 | 종류 | 도구 | 산출 |
|---|---|---|---|
| S1. ocr | 외부 | run_*_ocr.py + Claude vision | `<article>/ocr/<engine>/<unit>.txt` |
| S2. consensus | 자동 | `consensus.py review` + `draft` | `review_*.md` + `<id>.high_fidelity.draft_v0.md` |
| H3. high_fidelity | **인간** | Soo가 ⚠️ 마커 해소 | `<id>.high_fidelity.md` (마커 없음) |
| S4. transform | 자동 | `transform_old_to_modern.py` | `<id>.modern_reading.md` (띄어쓰기 미부여) |
| S5. spacing | 자동 | `add_spacing.py` (Claude API) | (3)에 띄어쓰기·구두점 부여 |
| H6. final | **인간** | Soo 검수 | frontmatter `status: human_verified` |

## 다음 단계

| 그룹 | 내용 |
|---|---|
| B1 (보류) | snudh GPU에 PaddleOCR 설치 (75편 일괄 시 GPU 가속 필요) |
| C (75편 일괄) | 시간순 정렬·series_index → 단 분리 → 위 파이프라인 적용 |

OCR runner의 article-agnostic화는 C 그룹 진입 시 함께 처리.

자세한 사양은 정책 v0.3 §3·§5 참조.
