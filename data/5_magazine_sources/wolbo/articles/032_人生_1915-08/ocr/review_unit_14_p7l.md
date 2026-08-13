# Review: unit_14_p7l

- Claude length: 290 chars
- Gemini length: 283 chars
- Paddle hanja length: 190 chars
- Diff regions (Claude vs Gemini): 25

## Diff table

| # | tag | Claude segment | Gemini segment | Paddle hanja support |
|---|---|---|---|---|
| 1 | replace | `義` | `異` | G:異 |
| 2 | replace | `了ᄒᆞ건` | `ᄒᆞ고` | C:了 |
| 3 | replace | `ᄒᆞᆷ은` | `야` | - |
| 4 | insert | `∅` | `의` | - |
| 5 | replace | `의` | `的` | G:的 |
| 6 | replace | `ᆫ` | `야` | - |
| 7 | replace | `는` | `ᄂᆞᆫ` | - |
| 8 | replace | `高` | `萬` | G:萬 |
| 9 | replace | `엿` | `얏` | - |
| 10 | delete | `의` | `∅` | - |
| 11 | delete | `의` | `∅` | - |
| 12 | replace | `償` | `債` | G:債 |
| 13 | replace | `로ᄒᆞ엿노라` | `ᄒᆞ니是로` | G:是 |
| 14 | replace | `로야千萬` | `ᄒᆞ야十方` | C:萬, G:十, G:方 |
| 15 | replace | `엿스리오` | `얏다라是` | G:是 |
| 16 | replace | `坤` | `坍` | G:坍 |
| 17 | replace | `된` | `部가` | G:部 |
| 18 | delete | `ᄒᆞ는時에法` | `∅` | C:時, C:法 |
| 19 | replace | `ᄃᆡ` | `되` | - |
| 20 | replace | `前` | `玆` | - |
| 21 | insert | `∅` | `樣` | G:樣 |
| 22 | replace | `을蹈` | `及歸` | G:及, G:歸 |
| 23 | replace | `의` | `的` | G:的 |
| 24 | insert | `∅` | `何某某` | G:何, G:某, G:某 |
| 25 | replace | `ᄒᆞᆷ에` | `意中` | G:中 |

## Heads
- Claude: `進退ᄒᆞᄂᆞᆫ義子를解明ᄒᆞ야要個를結了ᄒᆞ건一、先覺魔라ᄒᆞᆷ은圓通原凡魔라ᄒᆞᆷ은事物上利害得失의影響으로關聯ᄒᆞ야恒樣人의目的距離方面에反對의拘碍的으로介`
- Gemini: `進退ᄒᆞᄂᆞᆫ異子를解明ᄒᆞ야要個를結ᄒᆞ고一、先覺魔라야圓通原凡魔라ᄒᆞᆷ은事物上利害得失의影響으로關聯ᄒᆞ야恒樣人의目的의距離方面에反對的拘碍的으로介立ᄒᆞ`
- Paddle: `牛進就见爲何某無强方法音摘要专活舞臺所的極樂世界习衆別樣子真個的魔爲魔原因及歸化然工事未牛時川法宝坍伏魔殿建築部家家然處處十方衆生魔海劫波淪古是古叫指挥专叫執行`
