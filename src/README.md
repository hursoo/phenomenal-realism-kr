# src/

재사용 가능한 Python 코드를 보관하는 폴더입니다.

## 예상 모듈

- `tokenizer.py` - 한자어 토큰화 함수
- `similarity.py` - 유사도 계산 함수
- `preprocessing.py` - 전처리 유틸리티
- `visualization.py` - 시각화 함수

## 사용 예시

```python
from src.tokenizer import extract_hanja_tokens
from src.similarity import calculate_jaccard

tokens_a = extract_hanja_tokens(text_a)
tokens_b = extract_hanja_tokens(text_b)
similarity = calculate_jaccard(tokens_a, tokens_b)
```
