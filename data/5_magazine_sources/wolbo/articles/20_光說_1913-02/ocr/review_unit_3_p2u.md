# Review: unit_3_p2u

- Claude length: 269 chars
- Gemini length: 299 chars
- Paddle hanja length: 178 chars
- Diff regions (Claude vs Gemini): 30

## Diff table

| # | tag | Claude segment | Gemini segment | Paddle hanja support |
|---|---|---|---|---|
| 1 | replace | `雜俎니` | `너` | - |
| 2 | replace | `歛傾` | `觀顧` | - |
| 3 | replace | `寶` | `의眞` | - |
| 4 | replace | `輪` | `匹` | G:匹 |
| 5 | replace | `八月十五夜의明月이라古人이여` | `匣가寒桂의散香을散策ᄒᆞ면서` | C:八, C:月, C:十, C:五, C:夜, C:明, C:月, C:古, C:人, G:寒, G:桂, G:散, G:香, G:散, G:策 |
| 6 | replace | `ᆼ` | `야八月十五夜의明月이라古人이月에對ᄒᆞ야` | G:八, G:月, G:十, G:五, G:夜, G:明, G:月, G:古, G:人, G:月, G:對 |
| 7 | replace | `고` | `며` | - |
| 8 | insert | `∅` | `의恨` | G:恨 |
| 9 | replace | `고` | `되` | - |
| 10 | insert | `∅` | `最` | - |
| 11 | replace | `ᆷ` | `옴` | - |
| 12 | insert | `∅` | `는` | - |
| 13 | replace | `燒` | `盛` | G:盛 |
| 14 | replace | `ᆫ` | `야` | - |
| 15 | replace | `으` | `이` | - |
| 16 | replace | `ᄡᅥ` | `쓰` | - |
| 17 | replace | `淸` | `라清` | G:清 |
| 18 | replace | `潋` | `澹` | G:澹 |
| 19 | replace | `桂` | `結` | C:桂 |
| 20 | replace | `ㅣ라ᄒᆞ며` | `라라ᄒᆞᆷ이` | - |
| 21 | replace | `리` | `ᆷ이` | - |
| 22 | insert | `∅` | `故` | G:故 |
| 23 | replace | `朦` | `卧聽` | C:朦, G:卧 |
| 24 | replace | `ᄒᆞᆫ春夜의光이오疎簾의間에一線漸移ᄒᆞᆷ은` | `月澹月이` | C:春, C:夜, C:光, C:簾, C:間, C:一, C:線, C:漸, C:移, G:月, G:澹, G:月 |
| 25 | replace | `暗香ᄒᆞ며` | `籠ᄒᆞ야` | C:香 |
| 26 | insert | `∅` | `漸移ᄒᆞ옴은春夜의` | G:漸, G:移, G:春, G:夜 |
| 27 | replace | `은` | `이오疎簾의間一線의凉光을` | G:簾, G:間, G:一, G:線, G:光 |
| 28 | replace | `遊` | `送` | G:送 |
| 29 | replace | `午` | `年` | C:午, G:年 |
| 30 | replace | `고` | `옴은夏夜` | G:夏, G:夜 |

## Heads
- Claude: `雜俎니라月의光金烏는魚龍國에歛傾ᄒᆞ고宇宙寶景이沉沉ᄒᆞᆫ際에東天扶桑의上一輪玉八月十五夜의明月이라古人이여溶溶히上ᄒᆞᆼ感慨를寄ᄒᆞ고離別을寄ᄒᆞ며詩趣를寄ᄒ`
- Gemini: `너라月의光金烏는魚龍國에觀顧ᄒᆞ고宇宙의眞景이沉沉ᄒᆞᆫ際에東天扶桑의上一匹玉匣가寒桂의散香을散策ᄒᆞ면서溶溶히上ᄒᆞ야八月十五夜의明月이라古人이月에對ᄒᆞ야感`
- Paddle: `吉興味寄特八月中夜月感慨寄叫離别恨寄叫詩趣八月十五夜年明月日古人月對非寒桂散香散策溶溶刮上喜景沉沉際東天扶桑上一匹玉月光金鳥鱼龍國倾五宇宙可市光隱隱送盛午狂熱消`
