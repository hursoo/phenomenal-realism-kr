# 편입할 때 다시 세어야 할 것

2026-08-12에 야뢰 34편 + 백두산인·창해거사 37편(모두 이돈화의 필명)을 새로 확보해
판독 중이다. 이것이 코퍼스에 들어오면 **86편이 157편이 되고, 지금 저장소·논문·발표문에
적힌 수치가 거의 전부 움직인다.**

수치는 여러 문서에 흩어져 있고 서로를 인용한다. 하나만 고치면 다른 데가 어긋난 채 남는다.
**이 문서가 그 목록이다.** 편입 작업은 이 표를 위에서 아래로 훑으며 한다.

> ⚠️ 편입 전에 반드시: **파생물을 다시 생성한 뒤** 수치를 읽는다. 손으로 고치면
> 파생물과 문서가 갈린다.
>
> ```bash
> python3 scripts/06_magazines/build_keyword_index.py
> python3 scripts/06_magazines/build_reading.py
> python3 scripts/06_magazines/build_corpus_status.py
> python3 scripts/06_magazines/audit_source_pages.py
> ```

---

## 1. 코퍼스의 크기

| 지금 | 편입 뒤 | 어디에 |
|---|---|---|
| 편 **86** | 157 | `README.md`(루트) · `wolbo/README.md` · `TRUST.md` · `docs/02b` · `docs/06` · `source_pages_audit.md` · `PLAN_full_corpus_release.md` · `screening_1922.md` · `verified_transcripts/README.md` |
| 초벌 **85편** / 전사 없음 1 | 156 / 1 | 같은 자리 |
| 1922-02 이전 **82편** | 114 | `TRUST.md` · `screening_1922.md` · `source_pages_audit.md` · `docs/02b` |
| 기간 1911-01 ~ **1922-05** | 그대로 | `wolbo/README.md` |
| 원본 지면 **479장** · 폴더 100 | 789장 · 폴더 171 | 루트 `README.md` · `wolbo/README.md` · `docs/02b` · `source_pages_audit.md` |

⚠️ **편 번호를 다시 매기지 않는다.** C1~C86은 여러 문서·DB·발표문이 이미 인용하고 있다.
새 편은 #87~#157로 뒤에 붙였다(76~86번 수동 발굴분의 선례).

## 2. 판독의 상태

| 지금 | 어디에 |
|---|---|
| 판독 단위 **584단** | `wolbo/README.md` · `TRUST.md` · `PLAN` |
| 초벌 마커 **14,588** | 루트 `README.md` · `wolbo/README.md` · `TRUST.md` · `docs/02b` · `docs/06` |
| 등급 분포 규칙 1,217 / 대장 1,948 / **C 8,570 / G 1,501** / 미해소 1,032 / 면주 320 | `TRUST.md` §2 · `docs/02b` |
| **기계가 고른 자리 69.0%** · 판단 불필요 21.7% · 미해소 7.1% | 루트 `README.md` · `TRUST.md` · `docs/02b` · `docs/06` |
| Gemini 빈 단위 **89/584 (15.2%)** · Claude 2 | `TRUST.md` · `wolbo/README.md` |
| 색인 출현 **1,219** (17낱말) | `wolbo/README.md` · `TRUST.md` |

🔴 **새 71편은 구분선 검출값으로 다시 잘랐다**(겹침 40px). 곧 단 수·마커 수의 성격이
기존 86편과 다르다. 합산할 때 **두 갈래를 갈라 적는 편이 정직하다** —
「고정값으로 자른 86편」과 「검출값으로 자른 71편」.

## 3. 정본과 대조

| 지금 | 어디에 |
|---|---|
| 정본 **9편**(C01·C30~C37) | 루트 `README.md` · `wolbo/README.md` · `TRUST.md` · `docs/02b` · `docs/06` · `scripts/06_magazines/README.md` |
| 대조 자리 **26**(screening은 29로 적음 — 미해결) | `TRUST.md` §3 |
| 3분법 어휘 후보 **10편** · 「三派」 **0회** | `screening_1922.md` · `TRUST.md` |

🔴 **3분법 재검색은 편입의 필수 단계다.** 「三派 0회」·「唯物論 첫 자리 1918-10」은
82편 위에서 낸 판정이며, **114편 위에서 다시 돌려야 한다.**

```bash
python3 scripts/06_magazines/screen_wolbo_keywords.py --root <작업폴더> --before 1922-02
```

여기서 무엇이 걸리면 발표문 3장의 판정이 직접 흔들린다.

## 4. 모집단 서술

| 지금 | 편입 뒤 |
|---|---|
| 「李敦化 본명 명의만」 | 본명 + 夜雷 + 白頭山人 + 滄海居士 |
| 총목록 138편(李敦化 98·夜雷 39·공동 1) | 영인본 목차 기준 **164편**(1922-02 이전) |
| 「82편에 없다」 = 전산화한 82편 | 「114편에 없다」로 사정권이 넓어진다 |

`TRUST.md` §3의 경고문, `source_pages_audit.md` §3.3의 표가 그 자리다.

## 5. 저장소 밖

| | 무엇 |
|---|---|
| `hyeonsang/outputs/paper_2026/appendix/FACTS.md` · `A_corpus.md` | 코퍼스 데이터시트 — 편수·기간·매체 |
| `hyeonsang/outputs/paper_2026/paper_draft.md` §2.1 | 모집단 160편(개벽 74 + 월보 86) |
| `hyeonsang/outputs/개념사반_심포/symposium_draft.md` | 「82편」·「86편」·`[^앞선자리]`·`[^전수와OCR]`·자료 서지 |
| `_ocr_experiments/.../unified_db_2026-05-19/` | `MA_YD_10-20_WB.xlsx` 재생성 — 자카드 수치가 전부 다시 나온다 |

⚠️ **통일 DB를 다시 만들면 논문의 자카드 수치가 움직인다.** 새 71편이 매개 후보에 들어오면
변 ①②③의 분포와 순위가 달라질 수 있다. 이것은 편수 서술을 고치는 일과 **성격이 다른
작업**이므로 따로 잡아야 한다.

---

## 순서

1. 새 71편 판독 완료 → 초벌본 생성
2. **파생물 재생성** (색인·읽기 본문·대시보드·지면 감사)
3. **3분법 재검색**을 새 범위에서 → 걸린 자리 지면 대조
4. 위 §1~§4의 수치를 파생물에서 읽어 문서에 반영
5. 통일 DB 재생성은 **별건**으로 (자카드가 움직인다)
