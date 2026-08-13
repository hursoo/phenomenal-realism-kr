# Review: unit_7_p4u

- Claude length: 303 chars
- Gemini length: 277 chars
- Paddle hanja length: 173 chars
- Diff regions (Claude vs Gemini): 27

## Diff table

| # | tag | Claude segment | Gemini segment | Paddle hanja support |
|---|---|---|---|---|
| 1 | delete | `雜俎` | `∅` | C:雜 |
| 2 | replace | `ᄒᆞᆯ수업스` | `긔不能ᄒᆞ` | G:不, G:能 |
| 3 | replace | `ᄒᆞ기` | `긔` | - |
| 4 | replace | `ᄒᆞ고` | `宮과` | - |
| 5 | replace | `ᄒᆞ기` | `긔` | - |
| 6 | replace | `며` | `니` | - |
| 7 | replace | `ᄂᆞᆫ一道光線이` | `는者ㅣ` | C:一, C:光, G:者 |
| 8 | insert | `∅` | ` ` | - |
| 9 | replace | `ᄂᆞᆫ變` | `는襲` | - |
| 10 | insert | `∅` | `兀然` | G:然 |
| 11 | replace | `의` | `之` | G:之 |
| 12 | insert | `∅` | `發` | - |
| 13 | replace | `ᄒᆞᄂᆞᆫ` | `之` | G:之 |
| 14 | replace | `에一을得ᄒᆞᄂᆞᆫ變頭이` | `一을得ᄒᆞ는所以` | C:一, C:得, C:頭, G:一, G:得, G:所, G:以 |
| 15 | replace | `아니ᄒᆞᄂᆞᆫ者는` | `不知ᄒᆞ는人은` | C:者, G:不, G:知, G:人 |
| 16 | replace | `人이라ᄒᆞ노` | `이니` | C:人 |
| 17 | replace | `ᄒᆞ라` | `어다` | - |
| 18 | insert | `∅` | `슈` | - |
| 19 | replace | `有ᄒᆞ니一은` | `ᄒᆞ니一曰` | C:有, C:一, G:一 |
| 20 | insert | `∅` | `的` | G:的 |
| 21 | replace | `는心` | `曰心的` | C:心, G:心, G:的 |
| 22 | replace | `의生活` | `的의生` | C:生, C:活, G:的, G:生 |
| 23 | replace | `ᄂᆞᆫ` | `는` | - |
| 24 | replace | `의生` | `的의` | C:生, G:的 |
| 25 | replace | `ᆫ` | `는` | - |
| 26 | replace | `니며` | `닌` | - |
| 27 | replace | `煙이` | `烟이愁` | G:烟 |

## Heads
- Claude: `雜俎共히電燈도此에與ᄒᆞᆯ수업스며焰火가與ᄒᆞ기不能ᄒᆞ고共히太陽의光도此에與ᄒᆞ기不能ᄒᆞ며余는寧히暗夜에得ᄒᆞᄂᆞᆫ一道光線이아니라思ᄒᆞ노라默念默念은心의`
- Gemini: `共히電燈도此에與긔不能ᄒᆞ며焰火가與긔不能宮과共히太陽의光도此에與긔不能ᄒᆞ니余는寧히暗夜에得ᄒᆞ는者ㅣ아니라思ᄒᆞ노라默念 默念은心의光을得ᄒᆞ는襲頭第一法이`
- Paddle: `草木禽默人類共得心的人此心光不知人實人間謂之中一得所以然獨坐古宇宙間最奥聖殿。法複社會相對差别混雜默念默念是心光得装頭第一活叫至支吾人人類獨点喜身的生活二日心的`
