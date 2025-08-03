# weat-analyze-api

### 로컬 환경에서 실행
```bash
# 가상환경 생성 및 활성화
$ python3 -m venv venv
$ source venv/bin/activate   # (Windows: venv\Scripts\activate)

# 필요한 패키지 설치
$ pip install fastapi uvicorn

# 서버 실행
$ uvicorn main:app --reload
```



### 도커를 사용하여 실행

```bash
# Docker 이미지 빌드
$ docker build -t weat-analyze-api .

# 컨테이너 실행
$ docker run -d -p 8000:8000 --name weather-api weat-analyze-api
```