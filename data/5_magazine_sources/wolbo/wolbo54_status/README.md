# 54편 검수 트랙의 상태 대장

월보 86편 가운데 **54편을 대상으로 한 검수 트랙**의 무결성 대장과 진척 기록이다.
2026-06-23 · 2026-07-16 산출물을 그대로 옮겼다.

여기 실은 까닭은 두 가지다. **① 원본 지면이 지금도 같은 파일인지 기계로 확인할 수 있게 하고,
② 「아직 안 했다」와 「조건이 갖춰질 때까지 막아 뒀다」가 다르다는 것을 보이기 위해서다.**

---

## 1. `wolbo54_verification_status.csv` — 지면 무결성

| | |
|---|---|
| 행 | **288면** (54편의 원본 지면 전부) |
| `hash_status` | **288면 모두 `ok`** — 기대 SHA-256과 실제가 일치 |
| 함께 대조 | 바이트 수 · 픽셀 크기 (`1500x2307` 형식) |

열은 `series_index · article_folder · title · cnts_id · source_folder · page_file ·
hash_status · expected_sha256 · actual_sha256 · expected_bytes · actual_bytes ·
expected_pixels · actual_pixels · unit_ids · unit_count_for_page · layout_visual_status ·
warning`이다.

**이 대장이 하는 일.** 판독의 근거가 되는 지면이 **수집한 그때 그 파일 그대로인지**를 남이
확인할 수 있다. [`../source_pages/`](../source_pages/)의 이미지를 받아 SHA-256을 내어
`expected_sha256`과 맞춰 보면 된다. 프론트매터의 `sources:`가 「어느 원본인가」를 말한다면 이
대장은 「**그 원본이 지금도 같은가**」를 말한다.

⚠️ **`layout_visual_status`는 288면 전부 `pending_visual_review`다.** 해시는 맞지만 **단 분리
결과를 눈으로 확인하는 절차는 아직 남아 있다.** 자르기가 어긋나 글자가 잘렸는지는 해시가 답하지
못한다.

⚠️ `warning` 열에 `cnts_id_null_named_source`가 40면 있다. 국립중앙도서관 자료ID가 비어 폴더
이름으로 원본을 특정한 경우다(C79~C86 구간이 여기 해당한다 — `../series_index.csv`의
`cnts_id`가 빈 편들이다).

---

## 2. `wolbo54_baseline_diff.md` · `wolbo54_analysis_delta.md` — v2가 왜 없는가

54편을 검수해 넣은 **v2 DB(`MA_YD_10-20_WB_v2.xlsx`)는 아직 만들지 않았다.** 두 문서가 그
이유를 적는다.

> `MA_YD_10-20_WB_v2.xlsx`가 아직 생성되지 않았다. **이는 정상 차단 상태다.**
> 54편 모두 `status: human_verified` 또는 `status: final`인 `*.high_fidelity.md`와
> unit marker를 갖추기 전까지 v2 DB를 만들지 않는다.

곧 **일부만 검수된 상태로 DB를 갈아 끼우지 않겠다는 결정**이다. 절반만 정본인 DB는 어느 수치가
무엇 위에 서 있는지를 흐린다.

`baseline_diff.md`에는 현재 DB(baseline)의 편별 행 수가 있다 — 전체 1,425행 · 86편, 대상
54편의 편별 내역. **v2가 만들어지면 이 표와 비교해 무엇이 얼마나 바뀌었는지 셀 수 있다.**

### 지금 상태

| | |
|---|---|
| 검수 완료 | **9편** (C01 + [`../verified_transcripts/`](../verified_transcripts/)의 8편) |
| v2 조건 | 54편 전부 |
| 현재 DB | **초벌 위에 서 있다** — C01만 정본이 반영됨 |

이 어긋남은 [`../verified_transcripts/README.md`](../verified_transcripts/README.md) §2에
자세히 적었다.

---

## 3. 경로 표기

두 `.md`의 경로(`_ocr_experiments/unified_db_2026-05-19/...`)는 **편자의 작업 환경 기준**이며 이
저장소의 구조와 다르다. 기록으로 읽어야 한다. 대응은
[`../verified_transcripts/MAP.csv`](../verified_transcripts/MAP.csv)를 참고.
