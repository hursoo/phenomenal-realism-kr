# 월보 54편 v2 분석 delta

- 작성일: 2026-06-23
- v2 DB: `_ocr_experiments/unified_db_2026-05-19/output/MA_YD_10-20_WB_v2.xlsx`
- v2 tokens: `_ocr_experiments/unified_db_2026-05-19/output/norm/tokens_월보_v2.csv`
- v2 windows: `_ocr_experiments/unified_db_2026-05-19/output/norm/tokens_월보_win_v2.csv`

## 상태

v2 DB가 아직 생성되지 않았다. 현재 논문의 월보 54편 관련 수치와 C72 해석은 provisional로 둔다.

필요 조건:
- 54편 모두 `status: human_verified` 또는 `status: final`인 `*.high_fidelity.md` 작성
- 전사 본문에 `[unit: unit_...]` marker 부여
- `python scripts/wolbo54_v2_workflow.py convert-v2` 실행
- `hanja` 패키지 설치 후 `tokens-v2` 실행
