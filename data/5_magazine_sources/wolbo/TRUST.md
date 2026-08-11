# 이 자료로 무엇을 말할 수 있고 무엇을 말할 수 없는가

『천도교회월보』 이돈화 86편은 **완성된 자료가 아니다.** 아홉 편만 사람이 전문을 원본
지면과 대조했고, 일흔여섯 편은 두 판독 엔진이 갈린 자리를 안은 초벌이며, 한 편은 아직
전사조차 하지 않았다. 그런데도 내놓는 것은, **완성될 때까지 기다리면 아무도 쓰지 못하기
때문**이다. 대신 **어디가 어느 등급인지를 글자마다 표시**했다.

먼저 세 문장이다.

1. **훑기·후보 좁히기는 초벌로 된다.** 어느 편에 어떤 어휘가 있는지 보는 일에 정본은
   필요 없다.
2. **빈도를 수치로 말하거나 「없다」고 단정하려면 엔진 합의 구간을 쓴다.** 「N회」가 아니라
   「하한 N회, 상한 M회」다.
3. **인용은 반드시 그 자리를 원본 지면과 대조한다.** 대조한 대목만
   [`verified_passages.md`](verified_passages.md)에 들어가며, 거기에 없으면 대조하지 않은
   것이다.

---

## 1. 무엇이 어디에 있나

| | 무엇 | 상태 |
|---|---|---|
| [`reading/`](reading/) | **읽을 수 있는 본문 86편** | 마커를 해소하고 해소 방식을 표시. 파생물 |
| [`keyword_index.csv`](keyword_index.csv) | **키워드 색인** — 한 행이 한 출현 | 엔진 원출력에서 셈 |
| [`CORPUS_STATUS.csv`](CORPUS_STATUS.csv) | **편별 대시보드** | 어느 편이 얼마나 무른가 |
| [`verified_transcripts/`](verified_transcripts/) | **정본 8편** (C30~C37) + `_ruleset.md`·`MAP.csv` | 사람이 전문 대조 |
| `articles/01_.../transcripts/article_01.high_fidelity.md` | 정본 1편 (C01) | 사람이 전문 대조 |
| `articles/*/transcripts/*.draft_v0.md` | **초벌 전사 85편** | 마커가 든 원본. 손대지 않는다 |
| `articles/*/ocr/` | **엔진 원출력** (Claude·Gemini·Paddle) | 색인이 세는 대상 |
| [`source_pages/`](source_pages/) | **원본 지면 스캔** | 최종 판정의 근거 |
| [`verified_passages.md`](verified_passages.md) | 대목별 원문 대조 기록 | 인용의 자격 |
| [`screening_1922.md`](screening_1922.md) | 1922년 이전 3분법 어휘 선별·전수 대조 | |
| [`marker_resolution_experiment.md`](marker_resolution_experiment.md) | 눈 판단을 기계가 어디까지 줄이는가 | |

**`reading/`과 두 CSV는 파생물이다.** 낡으면 고치지 말고 다시 생성한다 — 고치면 원본과
어긋나고, 어긋난 사실이 아무 데도 남지 않는다.

```bash
python3 scripts/06_magazines/build_keyword_index.py     # keyword_index.csv
python3 scripts/06_magazines/build_reading.py           # reading/
python3 scripts/06_magazines/build_corpus_status.py     # CORPUS_STATUS.csv
```

---

## 2. 등급 — 이 글자를 누가 정했는가

`reading/`의 본문에는 마커를 해소한 자리마다 표시가 붙는다.

| 표시 | 누가 정했나 | 얼마나 믿을 것인가 |
|---|---|---|
| 표시 없음 | 두 엔진이 애초에 같이 읽었다 | 마커가 서지 않은 자리다. **그래도 미검수다** — 둘이 함께 틀릴 수 있다 |
| 〔규칙〕 | 규약 | 정자표 12쌍·공백 차이일 뿐이라 판단이 필요 없다(`_ruleset.md` §2·§3) |
| 〔대장〕 | 사람 — 다른 자리에서 | 정본에서 **같은 갈림**을 사람이 이미 결정했다(`marker_decisions.csv`). **이 자리를 본 것은 아니다** |
| 〔C〕〔G〕 | 기계 | 규칙 밖이라 한 엔진의 판독을 그대로 썼다. **근거가 없다** |
| 〔?C:…\|G:…〕 | 아무도 | 대분기(한쪽이 15자 이상) — 문단째 갈렸다. 고르지 않고 둘 다 남겼다 |
| 〔확인〕 | 사람 — 이 자리에서 | 그 자리를 원본 지면과 대조했다([`screening_1922.md`](screening_1922.md) §3-1) |
| `<n>` | — | 원문 쪽 경계. 앞이 n쪽이다 |

정본 9편에는 표시가 없다. 파일 이름이 `.정본.md`이고 머리글이 그렇게 밝힌다.

**자동 해소한 것을 「확인」이라 부르지 않는다.** 〔규칙〕과 〔대장〕은 사람의 손이 닿은
규약을 옮긴 것이지 그 자리를 본 것이 아니다.

### 실측 (2026-08-12)

초벌 76편 본문의 마커 **14,588**개가 이렇게 갈린다.

| 등급 | 자리 | 비율 |
|---|---:|---:|
| 〔규칙〕 판단 불필요 | 1,217 | 8.3% |
| 〔대장〕 정본의 결정을 옮김 | 1,948 | 13.4% |
| 〔C〕 Claude 판독 | 8,570 | 58.7% |
| 〔G〕 Gemini 판독 | 1,501 | 10.3% |
| 〔?…〕 대분기 — 미해소 | 1,032 | 7.1% |
| 면주·면번호 분리 | 320 | 2.2% |

**열 자리 가운데 일곱이 기계의 선택이다.** 이 비율이 이 코퍼스의 실상이며, 편별 편차는
[`CORPUS_STATUS.csv`](CORPUS_STATUS.csv)의 `auto_ratio`·`big_diff_ratio`에 있다. 대분기가
몰린 편(C60 64.9% · C55 50.0% · C64 20.5% · C40 16.2%)은 근접독해가 먼저 필요한 편이다.

---

## 3. 수치로 말하려면

### 색인은 두 엔진을 각각 센다

`keyword_index.csv`는 **합의본이 아니라 엔진 원출력**을 센다. 합의본을 단순 검색하면
**마커가 낱말 한가운데를 지나 체계적으로 과소 계수**하기 때문이다
([`screening_1922.md`](screening_1922.md) §2).

| `engine_agreement` | 뜻 | 쓰임 |
|---|---|---|
| `both` | 같은 단위에서 두 엔진이 함께 읽었다 | **하한**에 든다 |
| `claude_only` / `gemini_only` | 한쪽만 읽었다 | 상한에는 들되 하한에는 못 든다 |
| `verified` | 정본에서 셌다 | 사람이 확정한 판 |

곧 **하한 = `both` + `verified`**, **상한 = 전체 행**이다. 구간으로 적는 도구가
`scripts/06_magazines/engine_agreement_counts.py`다.

### 「없다」는 가장 조심할 판정

- **Gemini는 584단 가운데 89단(15.2%)을 빈 출력으로 남겼다**(Claude는 2단). 그 구간에서
  「없음」은 **「없다」가 아니라 「보지 않았다」**다. `CORPUS_STATUS.csv`의
  `gemini_empty_units`가 편별 수치다.
- 두 엔진이 **함께 놓친 것**은 어느 방법으로도 잡히지 않는다. 색인은 후보를 좁히는
  도구이며 판정은 지면에서 선다.
- 한 편(C10)은 전사가 아예 없다. 「86편에 없다」고 말할 때 그 한 편은 **찾아본 적이 없는**
  편이다.
- 🔴 **86편은 이돈화의 월보 글 전부가 아니다.** 총목록에서 필자가 李敦化로 걸린 글은
  **138편**(1922년 2월 이전 **124편**)이고, NL이 디지털로 제공해 내려받은 것이 그 일부다.
  곧 「82편에 없다」는 **「본 연구가 전산화한 82편에 없다」**이지 「1922년 2월 이전 이돈화의
  글에 없다」가 아니다. 자세한 것은 [`source_pages_audit.md`](source_pages_audit.md) §3.

「없다」에 가장 가까운 진술은 **두 엔진의 원출력 어디에도 없다**이다. 「三派」가 그런
경우다 — 두 판 전부에서 0회이며, 그래서 `keyword_index.csv`에 한 행도 없다.

### 이미 대조를 마친 자리

2026-08-11에 1922년 2월 이전 82편을 훑어 3분법 계열 어휘가 걸린 **10편의 모든 출현을
원본 지면과 대조**했다. 판독 오류는 하나도 없었다([`screening_1922.md`](screening_1922.md)
§3-1). 색인에서 `grade=대조`인 행이 그것이며 **오늘 다시 세니 26자리**다.

> ⚠️ `screening_1922.md` §3-1은 이를 **29자리**로 적었다. 오늘 두 가지 방법(색인의
> 단위별 짝짓기, 마커를 두 판으로 편 최대치)으로 다시 세었으나 둘 다 26이 나왔다.
> **판정(판독 오류 0·3분법 없음)은 흔들리지 않으나 자릿수는 맞춰야 한다.** 어느 쪽이
> 맞는지는 대조 당시의 기록으로 확인할 일로 남긴다.

---

## 4. 인용의 절차

1. `reading/`이나 색인에서 대목을 찾는다.
2. [`source_pages/`](source_pages/)에서 **그 지면을 연다.** 어느 편의 몇 쪽인지는
   색인의 `journal_page`와 각 편 `meta.yaml`이 가리킨다.
3. 한 글자씩 맞춘다. 세로쓰기 종성이 흐릿하면 **컬럼 단위로 잘라 3~4배로 확대**한다
   (`png_crop.py`·`detect_columns.py`, 근거는
   [`marker_resolution_experiment.md`](marker_resolution_experiment.md) §3).
4. 결과를 [`verified_passages.md`](verified_passages.md)에 적는다. **일치했다는 사실도
   적는다** — 대조하지 않은 것과 대조해서 맞았던 것은 다르다.

---

## 5. 이 문서가 모은 것

흩어져 있던 것을 한자리에 모았다. 각각의 원 기록은 그대로 있다.

- [`verified_transcripts/README.md`](verified_transcripts/README.md) §2 — 정본이 아직
  코퍼스에 들어가 있지 않다는 사실
- [`screening_1922.md`](screening_1922.md) §2 — 마커가 낱말을 쪼갠다
- [`../../../docs/02b_digitization_magazines.md`](../../../docs/02b_digitization_magazines.md)
  §2 — 판독 절차와 검수 현황
- [`marker_resolution_experiment.md`](marker_resolution_experiment.md) — 눈 판단을
  기계가 어디까지 줄이는가
- [`../../../docs/06_ai_disclosure.md`](../../../docs/06_ai_disclosure.md) — 어느 대목에
  기계가 관여했는가
