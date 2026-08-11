# Review: unit_5_p3u

- Claude length: 287 chars
- Gemini length: 265 chars
- Paddle hanja length: 156 chars
- Diff regions (Claude vs Gemini): 29

## Diff table

| # | tag | Claude segment | Gemini segment | Paddle hanja support |
|---|---|---|---|---|
| 1 | delete | `라` | `∅` | - |
| 2 | replace | `ᄒᆞ` | `호` | - |
| 3 | replace | `ᄒᆞ` | `호` | - |
| 4 | replace | `ᄒᆞ` | `호` | - |
| 5 | insert | `∅` | `天` | G:天 |
| 6 | replace | `ᄒᆞ` | `호` | - |
| 7 | replace | `ᄒᆞᄂᆞ니` | `호는디` | - |
| 8 | replace | `ᄒᆞ` | `호` | - |
| 9 | insert | `∅` | `且` | G:且 |
| 10 | replace | `ᄒᆞᆷ` | `홈` | - |
| 11 | replace | `ᄒᆞ깃` | `호일` | - |
| 12 | replace | `ᄒᆞ` | `호` | - |
| 13 | replace | `ᄒᆞ` | `호` | - |
| 14 | replace | `ᄒᆞ` | `호` | - |
| 15 | replace | `ᄒᆞ` | `호` | - |
| 16 | replace | `ᄒᆞᆷ` | `홈` | - |
| 17 | replace | `브` | `부` | - |
| 18 | replace | `ᄒᆞ` | `호` | - |
| 19 | replace | `ᄒᆞ노니` | `호는디` | - |
| 20 | insert | `∅` | `이` | - |
| 21 | replace | `ᄒᆞ야` | `호는光이나` | G:光 |
| 22 | replace | `ᄒᆞ` | `타호` | - |
| 23 | replace | `螢의光` | `蠻의光 ` | C:螢, C:光, G:光 |
| 24 | replace | `ᄒᆞᆫ` | `호는` | - |
| 25 | replace | `으로ᄒᆞ` | `에從호` | G:從 |
| 26 | replace | `ᄒᆞᄂᆞ니라` | `호는디行` | G:行 |
| 27 | replace | `ᄒᆞ에從ᄒᆞ야段段` | `홈으로란포에` | C:從, C:段, C:段 |
| 28 | replace | `ᄒᆞᄂᆞ니라燈이` | `호고란포도亦` | C:燈, G:亦 |
| 29 | replace | `ᄒᆞ` | `홈으` | - |

## Heads
- Claude: `雜俎的이니라是가世人이月의夜는愛ᄒᆞ되星의夜를不知ᄒᆞ는所以로다無月晴天의夜에妙高의臺上에登臨ᄒᆞ면下의星宿ㅣ盡皆眞面目을肉眼의前에發輝ᄒᆞ야來ᄒᆞᄂᆞ니宇宙의`
- Gemini: `雜俎的이니是가世人이月의夜는愛호되星의夜를不知호는所以로다無月晴天의夜에妙高의臺上에登臨호면天下의星宿ㅣ盡皆眞面目을肉眼의前에發輝호야來호는디宇宙의大호며且遠홈`
- Paddle: `进化亦不滿足言從段段進化行燈不滿足螢光人力所作光亦進化法則可光满足方日月星天人與光八此自然花南枝先開北枝移古光明音願言多数生物至情梅人光趁奔者盖暗黑不希更引詩的`
