# Review: oldhangul_unit_1_p1u

- Claude length: 198 chars
- Gemini length: 194 chars
- Paddle hanja length: 153 chars
- Diff regions (Claude vs Gemini): 16

## Diff table

| # | tag | Claude segment | Gemini segment | Paddle hanja support |
|---|---|---|---|---|
| 1 | delete | `新年에對ᄒᆞᆫ新感想으로新發明을公告ᄒᆞᆷ李敦化` | `∅` | C:新, C:年, C:對, C:新, C:感, C:想, C:新, C:發, C:明, C:公, C:告 |
| 2 | replace | `-奧菱` | `ㅣ與姜` | G:姜 |
| 3 | delete | `神` | `∅` | C:神 |
| 4 | replace | `眞` | `貞` | G:貞 |
| 5 | replace | `日` | `曰` | C:日 |
| 6 | delete | `神` | `∅` | C:神 |
| 7 | replace | `ᄒᆞ리` | `호되` | - |
| 8 | insert | `∅` | `ㅣ` | - |
| 9 | delete | `一日` | `∅` | C:日 |
| 10 | replace | `ᄒᆞ고` | `오且` | - |
| 11 | replace | `爾` | `雨` | G:雨 |
| 12 | replace | `者` | `若` | G:若 |
| 13 | replace | `啓` | `塔` | C:啓 |
| 14 | delete | `神` | `∅` | C:神 |
| 15 | replace | `眞` | `貞` | G:貞 |
| 16 | insert | `∅` | `講演新年에對ᄒᆞᆫ新感想으로新發明을公告ᄒᆞᆷ講 黃` | G:講, G:演, G:新, G:年, G:對, G:新, G:感, G:想, G:新, G:發, G:明, G:公, G:告, G:講 |

## Heads
- Claude: `新年에對ᄒᆞᆫ新感想으로新發明을公告ᄒᆞᆷ李敦化神師-奧菱時元으로至靑松ᄒᆞ니大神師忌日이隔數日이라道人沈時眞이告神師日大神師忌日이載迫일새略具祭品而來ᄒᆞ리라`
- Gemini: `神師ㅣ與姜時元으로至靑松ᄒᆞ니大師忌日이隔數日이라道人沈時貞이告神師曰大師忌日이載迫일새略具祭品而來호되라神師ㅣ曰此近에無靜潔行祀之處오且且連日大雨ᄒᆞ야水漲이`
- Paddle: `支司外神師-日此近叫無静潔行祀之處日大神師忌日载迫略具祭品而来忌日隔数日道人沈時貞告神師神师-奥姜時元星至青松吉山大神師古立翌日可還家亨叶乃以沈時真所備祭品星行`
