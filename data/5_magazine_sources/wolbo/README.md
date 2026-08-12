# 『천도교회월보』 이돈화 86편

1911년 1월부터 1922년 5월까지 『천도교회월보(天道敎會月報)』에 실린 이돈화의 글 86편이다.
국립중앙도서관이 제공하는 지면 스캔을 받아 **세로쓰기 옛한글 지면을 판독**해 텍스트로
만들었다. 판독 절차는 [`../../../docs/02b_digitization_magazines.md`](../../../docs/02b_digitization_magazines.md)
§2에 있다.

**이 자료는 미완이다.** 아홉 편만 사람이 전문을 원본과 대조했고, 일흔여섯 편은 두 엔진이
갈린 자리를 안은 초벌이며, 한 편(C10)은 아직 전사하지 않았다. 그런데도 전부 내놓는다.
**대신 어디가 어느 등급인지를 글자마다 표시했다.**

> 📌 **먼저 읽을 것 — [`TRUST.md`](TRUST.md).** 이 자료로 무엇을 말할 수 있고 무엇을 말할
> 수 없는지가 거기 있다. 특히 **빈도를 수치로 말하거나 「없다」고 단정하거나 인용하려는**
> 경우에는 반드시 읽어야 한다.

---

## 어디부터 볼까

| 하려는 일 | 갈 곳 |
|---|---|
| **그냥 읽고 싶다** | [`reading/`](reading/) — 86편, 마커를 해소한 본문 |
| **어떤 낱말이 언제 어디에 나오는지 보고 싶다** | [`keyword_index.csv`](keyword_index.csv) — 한 행이 한 출현 |
| **어느 편이 얼마나 믿을 만한지 보고 싶다** | [`CORPUS_STATUS.csv`](CORPUS_STATUS.csv) — 편별 대시보드 |
| **인용하려 한다** | [`TRUST.md`](TRUST.md) §4 → [`source_pages/`](source_pages/) → [`verified_passages.md`](verified_passages.md) |
| **원본 그대로가 필요하다** | `articles/*/transcripts/`(초벌) · `articles/*/ocr/`(엔진 원출력) |
| **이돈화가 월보에 쓴 글 전체를 보고 싶다** | [`yidonhwa_articles_index.md`](yidonhwa_articles_index.md) — 창간~1922-05, 168편, 확보 여부까지 |
| **새 71편 편입 때 무엇을 다시 세나** | [`RECOUNT.md`](RECOUNT.md) |
| **지면 폴더가 무엇인지 알고 싶다** | [`source_pages_audit.md`](source_pages_audit.md) · [`source_pages_MAP.csv`](source_pages_MAP.csv) |

---

## 폴더

```
wolbo/
├── TRUST.md                  ★ 신뢰 등급 안내 — 먼저 읽는다
├── reading/                  ★ 읽을 수 있는 본문 86편 (파생물)
├── keyword_index.csv         ★ 키워드 색인 — 한 행이 한 출현 (파생물)
├── CORPUS_STATUS.csv         ★ 편별 대시보드 (파생물)
│
├── articles/                 85편의 원본 산출 — 손대지 않는다
│   └── <NN>_<제목2자>_<연월>/
│       ├── meta.yaml         서지·지면 좌표·단 분리 좌표·해시
│       ├── units/            단 이미지 (*.png는 저장소에 싣지 않는다)
│       ├── ocr/              엔진 원출력 — claude_opus_4_7 · gemini · paddle · gpt5
│       └── transcripts/      초벌(*.draft_v0.md) — ⚠️ 마커가 든 판
│
├── verified_transcripts/     ★ 정본 8편 (C30~C37) + _ruleset.md · MAP.csv
├── source_pages/             ★ 원본 지면 스캔 479장 — 최종 판정의 근거
│   ├── NN_슬러그_YYYY-MM/     편 86 (전사 작업 폴더와 같은 이름)
│   ├── _중복/                지면이 바이트 단위로 같은 폴더 10
│   └── _편외/                코퍼스에 없는 글 3 + 별판 1
├── yidonhwa_articles_index.md/.tsv  ★ 이돈화 명의 전체 목록 (창간~1922-05, 168편)
├── source_pages_audit.md     ★ 그 100폴더가 각각 무엇인가 (편 86·중복 10·별판 1·편외 3)
├── source_pages_MAP.csv      위 감사의 기계 판독본
├── verified_passages.md      대목별 원문 대조 기록 — 인용의 자격
├── screening_1922.md         1922년 이전 3분법 어휘 선별·전수 대조
├── marker_resolution_experiment.md   눈 판단을 기계가 어디까지 줄이는가
├── marker_decisions.csv      결정 대장 — 정본에서 뽑은 「사람은 이렇게 정했다」
├── series_index.csv/.md      86편 시간순 목록
├── wolbo54_status/           54편 검수 트랙의 상태 기록
└── samples/                  옛한글·정책 측정용 부 표본
```

정본 1편(C01)은 예외로 `articles/01_kwonyu_1911-01/transcripts/article_01.high_fidelity.md`에
있다. 곧 **정본은 모두 아홉 편**이다.

🔴 **86편은 이돈화의 월보 글 전부가 아니다.** 총목록 기준 138편(1922년 2월 이전 124편)
가운데 국립중앙도서관이 디지털로 제공한 것을 받아 정착시킨 것이 86편이다. 게다가
**지면이 이미 여기 있는데도 코퍼스에 없는 이돈화 글이 둘 있다**(「我觀苦樂論」 1913-07 ·
「偉大ᄒᆞᆫ 心의 世界」 1918-04). 근거와 남은 판단은
[`source_pages_audit.md`](source_pages_audit.md).

---

## 실측 (2026-08-12)

| | |
|---|---:|
| 편 | **86** (정본 9 · 초벌 76 · 전사 없음 1) |
| 기간 | 1911-01-15 ~ 1922-05-15 |
| 원본 지면 스캔 | 479장 (폴더 100 = 편 86 · `_중복/` 10 · `_편외/` 4) |
| 판독 단위 | 584단 |
| 초벌본의 마커(엔진이 갈린 자리) | 14,588 |
| 그 가운데 **기계가 한쪽을 고른 자리** | 10,071 (69.0%) |
| 고르지 못한 자리(대분기) | 1,032 (7.1%) |
| Gemini 빈 출력 단위 | 89 (15.2%) — 그 구간의 「없음」은 「보지 않았음」이다 |
| 색인이 잡은 출현 | 1,219 (17낱말) |

---

## 파생물은 다시 생성한다

`reading/`·`keyword_index.csv`·`CORPUS_STATUS.csv`는 **파생물**이다. 낡거나 틀리면 고치지
말고 다시 만든다. 고치면 원본과 어긋나고, 어긋난 사실이 아무 데도 남지 않는다.

```bash
python3 scripts/06_magazines/build_keyword_index.py    # 색인
python3 scripts/06_magazines/build_reading.py          # 읽기 본문
python3 scripts/06_magazines/build_corpus_status.py    # 대시보드
python3 scripts/06_magazines/audit_source_pages.py     # 지면 폴더 감사
```

도구 전체가 어떤 순서로 쓰이는지는 **[`scripts/06_magazines/README.md`](../../../scripts/06_magazines/README.md)**
— 지면을 단으로 가르고(①) 판독하고(②) 무른 데를 찾고(③) 밀어 올리고(④) 재고(⑤)
내놓는(⑥) 여섯 단계로 적어 두었다.

세 스크립트 모두 의존성이 없다(표준 라이브러리 + PyYAML). 마커 해소 규약은
`scripts/06_magazines/wolbo_markers.py`가 `verified_transcripts/_ruleset.md`를 코드로 옮긴
것이며, **규약이 권위이고 코드가 그것을 따른다.**
