# app/

Streamlit 발표용 웹앱 관련 파일을 보관하는 폴더입니다.

## 구조

```
app/
├── app.py              # 메인 Streamlit 앱
├── requirements.txt    # 앱 의존성
├── data/               # 앱에서 사용하는 데이터 (사본)
├── images/             # 앱에서 사용하는 이미지
└── html_assets/        # 인터랙티브 HTML 파일
```

## 실행 방법

```bash
cd app
streamlit run app.py
```

## 참고

- 기존 지인 검토용: `hursoo/digital-philology`
- 이 폴더는 정식 발표용 버전 개발
