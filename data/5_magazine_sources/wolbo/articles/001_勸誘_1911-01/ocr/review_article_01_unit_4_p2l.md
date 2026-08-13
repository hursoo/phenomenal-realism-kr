# Review: article_01_unit_4_p2l

- Claude length: 332 chars
- Gemini length: 313 chars
- Paddle hanja length: 219 chars
- Diff regions (Claude vs Gemini): 32

## Diff table

| # | tag | Claude segment | Gemini segment | Paddle hanja support |
|---|---|---|---|---|
| 1 | insert | `∅` | `니` | - |
| 2 | insert | `∅` | `며知足이` | G:知, G:足 |
| 3 | delete | `知足이어니` | `∅` | C:知, C:足 |
| 4 | replace | `란` | `는天` | G:天 |
| 5 | replace | `飲` | `飮` | C:飲 |
| 6 | replace | `ᄒᆞ` | `이` | - |
| 7 | insert | `∅` | `ᆫ` | - |
| 8 | replace | `事業` | `其樂` | C:事, C:業, G:其, G:樂 |
| 9 | insert | `∅` | `ᆫ` | - |
| 10 | insert | `∅` | `나` | - |
| 11 | delete | `을不知ᄒᆞ고塵埃에` | `∅` | C:不, C:知, C:塵, C:埃 |
| 12 | insert | `∅` | `ᆫ` | - |
| 13 | insert | `∅` | `塵埃가` | G:塵, G:埃 |
| 14 | replace | `되` | `야到` | G:到 |
| 15 | replace | `洒` | `酒` | G:酒 |
| 16 | replace | `를` | `룰` | - |
| 17 | replace | `甚` | `는其` | C:甚, G:其 |
| 18 | replace | `質` | `貿` | - |
| 19 | replace | `市` | `苛` | C:市 |
| 20 | replace | `既` | `旣` | C:既 |
| 21 | replace | `ᄒᆞ면` | `라` | - |
| 22 | replace | `를不` | `룰何` | C:不, G:何 |
| 23 | replace | `ᄒᆞ며其心既` | `며其心旣` | C:其, C:心, C:既, G:其, G:心 |
| 24 | replace | `를` | `룰` | - |
| 25 | replace | `觀` | `棘` | - |
| 26 | replace | `至焉` | `야` | C:至, C:焉 |
| 27 | replace | `이며` | `ᄒᆞ며一動에` | G:一, G:動 |
| 28 | insert | `∅` | `ᄒᆞ` | - |
| 29 | replace | `며言念到此에` | `다가` | C:言, C:念, C:到, C:此 |
| 30 | replace | `ᄒᆞ야` | `로` | - |
| 31 | insert | `∅` | `에` | - |
| 32 | delete | `page_number: 二六` | `∅` | - |

## Heads
- Claude: `며知止어니其貴란天爵이어니知足이어니其富란天大라陋巷瓢飲에曲肱枕之도樂在其中이며風風雨雨에草行露宿도樂在其中ᄒᆞ니故로其樂을知ᄒᆞ者ㅣ事業을能成ᄒᆞ고事業을不知`
- Gemini: `며知止어니니其貴란天爵이며知足이어니其富는天天大라陋巷瓢飮에曲肱枕之도樂在其中이며風風雨雨에草行露宿도樂在其中이니故로其樂을知ᄒᆞᆫ者ㅣ事業을能成ᄒᆞ고其樂을不`
- Paddle: `堆積到一番酒掃喜不加甚则我心量西古今聖賢豪傑此樂中出來直者呈樂量不知者—事業不成山乃知束故其樂知直者-事业能成专其中国叫風風雨雨草行露宿丘樂在其中富天大陋巷瓢飲`
