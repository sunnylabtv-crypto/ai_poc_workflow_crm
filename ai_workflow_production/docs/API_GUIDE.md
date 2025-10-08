# 📚 API 설정 가이드

## 🔧 Gmail API 설정

### 1. Google Cloud Console 설정
1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. **API 및 서비스 → 라이브러리** 이동
4. "Gmail API" 검색 후 활성화

### 2. OAuth 2.0 인증 정보 생성
1. **API 및 서비스 → 사용자 인증 정보** 이동
2. **+ 사용자 인증 정보 만들기 → OAuth 클라이언트 ID** 선택
3. 애플리케이션 유형: **데스크톱 애플리케이션**
4. 이름: `Gmail-Workflow-Client`
5. **만들기** 클릭
6. JSON 파일 다운로드 → 상위 폴더에 `credentials_new.json`으로 저장

### 3. OAuth 동의 화면 설정
1. **OAuth 동의 화면** 메뉴 이동
2. 사용자 유형: **외부** 선택
3. 앱 정보 입력
4. 범위 추가:
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/gmail.send`
5. 테스트 사용자에 본인 이메일 추가

## 🤖 Gemini API 설정

### 1. API 키 발급
1. [Google AI Studio](https://makersuite.google.com/app/apikey) 접속
2. **Create API key** 클릭
3. 생성된 API 키 복사

### 2. 환경변수 설정
상위 폴더의 `.env` 파일에 추가:
```bash
GEMINI_API_KEY=your_api_key_here