# Review: unit_11_p6u

- Claude length: 249 chars
- Gemini length: 227 chars
- Paddle hanja length: 132 chars
- Diff regions (Claude vs Gemini): 15

## Diff table

| # | tag | Claude segment | Gemini segment | Paddle hanja support |
|---|---|---|---|---|
| 1 | delete | `敎理部` | `∅` | C:理, C:部 |
| 2 | replace | `義` | `味` | G:味 |
| 3 | delete | `느` | `∅` | - |
| 4 | replace | `二` | `神으` | G:神 |
| 5 | replace | `ᄒᆞᆷ` | `홈` | - |
| 6 | replace | `ᄒᆞᆷ` | `宮` | - |
| 7 | replace | `ᄉᆔ生ᄒᆞ야無意味에` | `서生ᄒᆞ야無意味로` | C:生, C:無, C:意, C:味, G:生, G:無, G:意, G:味 |
| 8 | replace | `은芥` | `우芬` | - |
| 9 | delete | `ᆫ` | `∅` | - |
| 10 | replace | `ᄒᆞᄂᆞᆫ` | `홈은` | - |
| 11 | replace | `ᄂᆞ` | `느` | - |
| 12 | replace | `ᄒᆞ되` | `키爲홈뿐이라何故로` | G:爲, G:何, G:故 |
| 13 | replace | `ᆷ뿐이라何故로人生은進化ᄒᆞᄂᆞ냐ᄒᆞ면人은神` | `느냐ᄒᆞ면人` | C:何, C:故, C:人, C:生, C:進, C:化, C:人, C:神, G:人 |
| 14 | insert | `∅` | `神에` | G:神 |
| 15 | replace | `야` | `며` | - |

## Heads
- Claude: `敎理部지로다風에因ᄒᆞ야成ᄒᆞ야風에因ᄒᆞ야沒ᄒᆞ니其裏에何等意義가有ᄒᆞ느냐人은神의泡라ᄒᆞ면二로因ᄒᆞ야組織된人이反히神에歸ᄒᆞᆷ에對ᄒᆞ야人其者의無意味ᄒ`
- Gemini: `지로다風에因ᄒᆞ야成ᄒᆞ야風에因ᄒᆞ야沒ᄒᆞ니其裏에何等意味가有ᄒᆞ냐人은神의泡라ᄒᆞ면神으로因ᄒᆞ야組織된人이反히神에歸홈에對ᄒᆞ야人其者의無意味宮이泡其者의`
- Paddle: `中京人神接近支叫直接神化爲高何故人生進化古吾人强答到人生進神出古反刮神叫师實何故人生出神歸事者外中但人生神子種左見出不能古人生目的月生無意味#死諸氏叫人生無意味`
