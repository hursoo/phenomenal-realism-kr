# Review: unit_1_p1u

- Claude length: 248 chars
- Gemini length: 241 chars
- Paddle hanja length: 121 chars
- Diff regions (Claude vs Gemini): 17

## Diff table

| # | tag | Claude segment | Gemini segment | Paddle hanja support |
|---|---|---|---|---|
| 1 | replace | `理部` | `門訂議` | G:門, G:訂, G:議 |
| 2 | replace | `는颶` | `눈에風` | G:風 |
| 3 | replace | `될` | `된` | - |
| 4 | replace | `될` | `된` | - |
| 5 | replace | `ᄐᆞ` | `토` | - |
| 6 | delete | `ᆯ` | `∅` | - |
| 7 | replace | `墮ᄒᆞᆯ` | `壓ᄒᆞ` | G:壓 |
| 8 | delete | `니` | `∅` | - |
| 9 | delete | `ᆯ` | `∅` | - |
| 10 | delete | `ᆯ` | `∅` | - |
| 11 | replace | `ᄃᆡ` | `딘` | - |
| 12 | replace | `에理` | `인聖` | G:聖 |
| 13 | delete | `ᆫ` | `∅` | - |
| 14 | delete | `로` | `∅` | - |
| 15 | replace | `홈에` | `ᄒᆞ는데` | - |
| 16 | delete | `함` | `∅` | - |
| 17 | delete | `ᆫ` | `∅` | - |

## Heads
- Claude: `敎理部구나우리는颶風迷津에船長될義務가有ᄒᆞ고黑雲昏衢에巨燭될意思도업지안ᄐᆞ다그러면萬羽(人名)가不拔ᄒᆞᆯ心과萬政(人名)이不墮ᄒᆞᆯ氣를미리定ᄒᆞ며正치아`
- Gemini: `敎門訂議구나우리눈에風風迷津에船長된義務가有ᄒᆞ고黑雲昏衢에巨燭된意思도업지안토다그러면萬羽(人名)가不拔ᄒᆞ心과萬政(人名)이不壓ᄒᆞ氣를미리定ᄒᆞ며正치아치`
- Paddle: `親近叫對古情操說罷喜常人常情向古外其秘密展示叫悲哀耀賢明讀者諸氏人鬱有志州大州圆洲外公中聖化會叫来叫大小叫方古中我心量夫心靓者目随長古短不壓氣量定正萬羽（人名）`
