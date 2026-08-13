# Review: unit_5_p3u

- Claude length: 388 chars
- Gemini length: 431 chars
- Paddle hanja length: 231 chars
- Diff regions (Claude vs Gemini): 44

## Diff table

| # | tag | Claude segment | Gemini segment | Paddle hanja support |
|---|---|---|---|---|
| 1 | delete | `講` | `∅` | C:講 |
| 2 | replace | `歎` | `觀` | G:觀 |
| 3 | insert | `∅` | `又` | G:又 |
| 4 | replace | `ᄒᆞ` | `等` | G:等 |
| 5 | delete | `가` | `∅` | - |
| 6 | replace | `라` | `타` | - |
| 7 | replace | `호` | `定` | G:定 |
| 8 | insert | `∅` | `ᆫ` | - |
| 9 | replace | `勤` | `動치` | G:動 |
| 10 | replace | `니` | `ᆫ` | - |
| 11 | insert | `∅` | `은此` | G:此 |
| 12 | insert | `∅` | `ᆫ事` | G:事 |
| 13 | replace | `ᄒᆞᆷ` | `舍` | - |
| 14 | insert | `∅` | `ᆯ` | - |
| 15 | insert | `∅` | `且` | - |
| 16 | replace | `得` | `爲` | C:得 |
| 17 | replace | `ᄒᆞ` | `의` | - |
| 18 | replace | `段` | `를伸야` | - |
| 19 | replace | `威壓` | `感應` | G:感, G:應 |
| 20 | replace | `은` | `ᄒᆞᆫ` | - |
| 21 | replace | `循` | `簡` | G:簡 |
| 22 | replace | `을` | `ᄒᆞ고` | - |
| 23 | replace | `纏結` | `輒繩` | C:結 |
| 24 | replace | `치는` | `한` | - |
| 25 | insert | `∅` | `是가吾` | G:是, G:吾 |
| 26 | insert | `∅` | `城砦이며避難所니라` | G:城, G:避, G:難, G:所 |
| 27 | replace | `吾人을라ᄉᆞ는 ` | `에養ᄒᆞ야再斷ᄒᆞᆯ바로다` | C:吾, C:人 |
| 28 | replace | `劍` | `關` | G:關 |
| 29 | replace | `을由ᄒᆞ야吾人을種` | `이理論그吾人을誘掖` | C:吾, C:人, G:理, G:論, G:吾, G:人 |
| 30 | replace | `케ᄒᆞᆯ` | `州ᄒᆞᄂᆞᆫ` | - |
| 31 | replace | `갓ᄋᆞᆷ` | `됨` | - |
| 32 | replace | `似` | `然` | G:然 |
| 33 | insert | `∅` | `平` | G:平 |
| 34 | replace | `눈舶` | `ᄂᆞᆫ巨艦` | - |
| 35 | replace | `葉을獻` | `裝ᄒᆞᆫ巖` | - |
| 36 | replace | `ᄒᆞ妻` | `表` | G:表 |
| 37 | replace | `야` | `ᆷ과` | - |
| 38 | replace | `활` | `히히` | - |
| 39 | replace | `活上現則이라ᄒᆞ면` | `燥케ᄒᆞᆯ뿐으로` | C:活, C:上, G:燥 |
| 40 | insert | `∅` | `與` | - |
| 41 | replace | `느` | `ᄂᆞ` | - |
| 42 | insert | `∅` | `라` | - |
| 43 | replace | `度ᄒᆞ` | `遠ᄒᆞᆫ` | C:度 |
| 44 | insert | `∅` | `活上規則이라도吾人의` | G:活, G:上, G:吾, G:人 |

## Heads
- Claude: `講演奮鬪ᄒᆞᄂᆞᆫ者로過去를顧ᄒᆞ고悲歎치안ᄂᆞᆫ者로何ᄒᆞ結果가가出來ᄒᆞᆯ지라도己의力으로如何키不能라思ᄒᆞ야泰然히此를受ᄒᆞᄂᆞᆫ大勇者로如斯히吾은安호平`
- Gemini: `演奮鬪ᄒᆞᄂᆞᆫ者로過去를顧ᄒᆞ고悲觀치안ᄂᆞᆫ者로又何等結果가出來ᄒᆞᆯ지라도己의力으로如何키不能타思ᄒᆞ야泰然히此를受ᄒᆞᄂᆞᆫ大勇者로如斯히吾은安定平和와`
- Paddle: `司吾人焦燥毫末吾人力壹吾人种益刊专材料外乏言怡然太洋漂签方中人生關理論理論工人号人牛苦戰疲時退力此處努力上第一步信仰叫城り叫避難所者又此代者無是。此簡單医實際生`
