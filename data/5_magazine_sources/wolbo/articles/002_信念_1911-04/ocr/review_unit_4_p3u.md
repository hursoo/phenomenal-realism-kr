# Review: unit_4_p3u

- Claude length: 241 chars
- Gemini length: 254 chars
- Paddle hanja length: 189 chars
- Diff regions (Claude vs Gemini): 18

## Diff table

| # | tag | Claude segment | Gemini segment | Paddle hanja support |
|---|---|---|---|---|
| 1 | insert | `∅` | `講演` | G:講, G:演 |
| 2 | replace | `爲` | `焉` | G:焉 |
| 3 | delete | `天` | `∅` | C:天 |
| 4 | insert | `∅` | `天` | G:天 |
| 5 | replace | `量을` | `臺를` | C:量 |
| 6 | replace | `더` | `되` | - |
| 7 | replace | `홈` | `ᄒᆞ` | - |
| 8 | replace | `巋` | `魑` | - |
| 9 | replace | `呑` | `吞` | G:吞 |
| 10 | replace | `ᅵ` | `一` | G:一 |
| 11 | replace | `敎건딕自天을自侍` | `教컨되自天을自恃` | C:自, C:天, C:自, C:侍, G:教, G:自, G:天, G:自 |
| 12 | insert | `∅` | `케` | - |
| 13 | replace | `ㅣ` | `一` | G:一 |
| 14 | replace | `敎` | `教` | G:教 |
| 15 | insert | `∅` | `虛信으로宗教名` | G:信, G:宗, G:教, G:名 |
| 16 | insert | `∅` | `ᆯ` | - |
| 17 | replace | `ㅣ` | `一` | G:一 |
| 18 | insert | `∅` | `ᆯ` | - |

## Heads
- Claude: `續ᄒᆞ다가其終은東天皓月이大夜暗光을破ᄒᆞ면其知爲往古來今이오其氣焉上天下地라浩浩然世界活精神이身邊靈量을作ᄒᆞ더萬幅雲帳이一朶寶玉을藏홈과恰似ᄒᆞ야其氣所到에`
- Gemini: `講演續ᄒᆞ다가其終은東天皓月이大夜暗光을破ᄒᆞ면其知焉往古來今이오其氣焉上下天地라浩浩然世界活精神이身邊靈臺를作ᄒᆞ되萬幅雲帳이一朶寶玉을藏ᄒᆞ과恰似ᄒᆞ야其氣`
- Paddle: `一觉高司宗教界諸氏吾最後大宗信念神聖義是永保叫個人幸福能享者一有二十世紀此時代明在专虚信宗教名之乎不者其虚信叫他信自至到京者一非吾教而其孰有自侍叫自信爸自篤列外`
