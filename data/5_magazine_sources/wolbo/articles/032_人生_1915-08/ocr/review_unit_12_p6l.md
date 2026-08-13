# Review: unit_12_p6l

- Claude length: 234 chars
- Gemini length: 234 chars
- Paddle hanja length: 147 chars
- Diff regions (Claude vs Gemini): 23

## Diff table

| # | tag | Claude segment | Gemini segment | Paddle hanja support |
|---|---|---|---|---|
| 1 | insert | `∅` | `訓` | - |
| 2 | delete | `訓 ` | `∅` | - |
| 3 | replace | `養培 ` | `塔` | C:養, C:培 |
| 4 | replace | `져` | `저` | - |
| 5 | replace | `엿다` | `야` | - |
| 6 | replace | `ᄒᆞᆯ` | `홈` | - |
| 7 | replace | `엿슨` | `얏뿐` | - |
| 8 | replace | `即` | `卽` | - |
| 9 | replace | `ᄃᆡ` | `듸` | - |
| 10 | replace | `ᄂᆞᆫ` | `는` | - |
| 11 | replace | `ᄲᅮᆫ이로다修養` | `뿐政治法律` | C:修, C:養, G:政, G:治, G:法, G:律 |
| 12 | replace | `政治` | `等諸` | C:政, C:治, G:等, G:諸 |
| 13 | delete | `等` | `∅` | C:等 |
| 14 | replace | `ᆯ條件에서` | `는間에肉體의保險品됨에셔` | C:條, G:間, G:肉, G:體, G:保, G:險, G:品 |
| 15 | replace | `硏` | `研` | G:研 |
| 16 | replace | `면` | `함이` | - |
| 17 | insert | `∅` | `ᄒᆞᆫ` | - |
| 18 | insert | `∅` | `뿐故` | G:故 |
| 19 | replace | `葉ᄒᆞᆫ` | `棄ᄒᆞ고` | - |
| 20 | replace | `도` | `되` | - |
| 21 | replace | `諫議` | `謙讓` | C:諫, C:議 |
| 22 | replace | `葉ᄒᆞᆫ嚴遯` | `棄ᄒᆞ고巖處` | C:嚴, G:處 |
| 23 | replace | `도` | `되` | - |

## Heads
- Claude: `奉訓 李養培 氏코져ᄒᆞᆫ神想에出ᄒᆞ엿다바라ᄒᆞᆯ지로다然ᄒᆞ면吾人은神의最高思에達키爲ᄒᆞ야無意味의生活을水劫以來로繼續ᄒᆞ엿슨此에人生의無意味의生活은即大`
- Gemini: `訓奉李塔氏코저ᄒᆞᆫ神想에出ᄒᆞ야바라홈지로다然ᄒᆞ면吾人은神의最高思에達키爲ᄒᆞ야無意味의生活을水劫以來로繼續ᄒᆞ얏뿐此에人生의無意味의生活은卽大意味의生活인`
- Paddle: `左有京諫議大夫嚴處士左有修其者故萬乘位大觉者不可人生可赤裸裸最終目的意味可生活大意味生活9#人生生活量水劫以来繼續此人生可無吾人神最高思叫達爲吉無意味神想出然（`
