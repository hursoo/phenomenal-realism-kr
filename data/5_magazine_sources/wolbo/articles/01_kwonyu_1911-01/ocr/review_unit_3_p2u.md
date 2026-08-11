# Review: unit_3_p2u

- Claude length: 320 chars
- Gemini length: 324 chars
- Paddle hanja length: 211 chars
- Diff regions (Claude vs Gemini): 28

## Diff table

| # | tag | Claude segment | Gemini segment | Paddle hanja support |
|---|---|---|---|---|
| 1 | insert | `∅` | `講演` | G:講 |
| 2 | insert | `∅` | `ᆫ` | - |
| 3 | replace | `吾` | `끔` | C:吾 |
| 4 | replace | `外` | `上` | C:外 |
| 5 | replace | `를` | `을` | - |
| 6 | replace | `而` | `則` | G:則 |
| 7 | replace | `ᆯ` | `ᆫ` | - |
| 8 | replace | `ᄒᆞᆷ` | `궁` | - |
| 9 | replace | `ᄒᆞᄒᆞ` | `得ᄒᆞᆯ` | G:得 |
| 10 | replace | `의` | `에` | - |
| 11 | insert | `∅` | `ᆫ分子天으로呈愁雲夜谷에鬼脉이陰陰ᄒᆞ며` | G:分, G:子, G:天, G:呈, G:愁, G:雲, G:夜, G:谷, G:鬼, G:脉, G:陰, G:陰 |
| 12 | replace | `ᄒᆞ慕` | `에暮` | G:暮 |
| 13 | replace | `雲夜谷에鬼脈이陰陰ᄒᆞ然則도다` | `이` | C:雲, C:夜, C:谷, C:鬼, C:陰, C:陰, C:然, C:則 |
| 14 | replace | `ᄒᆞ` | `沉ᄒᆞᆫ` | G:沉 |
| 15 | replace | `를보` | `을呈` | G:呈 |
| 16 | replace | `는` | `ᄂᆞᆫ` | - |
| 17 | replace | `ᄒᆞ樂이라` | `의樂과` | C:樂, G:樂 |
| 18 | replace | `는` | `ᄂᆞᆫ` | - |
| 19 | replace | `ᄒᆞ` | `之` | G:之 |
| 20 | replace | `ᄒᆞ면` | `之則` | G:之, G:則 |
| 21 | replace | `意` | `斷` | G:斷 |
| 22 | replace | `라ᄒᆞ` | `로다` | - |
| 23 | delete | `ᄒᆞ` | `∅` | - |
| 24 | replace | `ᄒᆞ` | `를` | - |
| 25 | replace | `知命이어니其囊란天又` | `天으로富貴를觀ᄒᆞ면` | C:知, C:命, C:其, C:天, C:又, G:天, G:富, G:貴, G:觀 |
| 26 | replace | `며` | `라` | - |
| 27 | replace | `囊` | `壽` | G:壽 |
| 28 | replace | `又` | `久` | C:又, G:久 |

## Heads
- Claude: `分을得ᄒᆞ지라도彼仰觀昭昭ᄒᆞ無數太陽界가吾의富貴的世界外의世界를成ᄒᆞ야無厭의慾線이又彼에向ᄒᆞ야一試를更加ᄒᆞ지니然而欲望을達ᄒᆞᆯ際限이無ᄒᆞᆷ으로極樂을`
- Gemini: `講演分을得ᄒᆞ지라도彼仰觀昭昭ᄒᆞᆫ無數太陽界가끔의富貴的世界上의世界을成ᄒᆞ야無厭의慾線이又彼에向ᄒᆞ야一試를更加ᄒᆞ지니然則欲望을達ᄒᆞᆫ際限이無궁으로極樂`
- Paddle: `則六合彌五捲之则方寸藏斷斷樂斗循時妄動性樂外放之在喜彼無根無源驚世自喜点客氣沉態是呈左然則吾所謂極樂何叫谷川鬼脉陰陰古叫日迫西山暮色沉徘徊古外此神明靈澈分子天愁`
