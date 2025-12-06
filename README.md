# Azure Authentication Module

Azure AD OAuth 2.0 인증을 처리하는 Python 모듈입니다.

## 기능

- Azure AD OAuth 2.0 인증 플로우 구현
- 액세스 토큰 및 리프레시 토큰 관리
- 사용자 정보 및 세션 관리
- 토큰 자동 갱신
- 다중 Azure AD 앱 지원

## 데이터베이스 구조

### azure_app_info
Azure AD 앱 정보를 저장합니다.
- application_id: Azure AD 애플리케이션 ID
- client_secret: 클라이언트 시크릿
- tenant_id: 테넌트 ID
- redirect_uri: 리다이렉트 URI

### azure_user_info
로그인한 사용자 정보를 저장합니다.
- object_id: 사용자 고유 ID
- user_email: 사용자 이메일
- display_name: 표시 이름
- 기타 프로필 정보

### azure_session_info
인증 토큰 및 세션 정보를 관리합니다.
- session_id: 세션 고유 ID
- access_token: 액세스 토큰
- refresh_token: 리프레시 토큰
- expires_at: 토큰 만료 시간

## 설치

1. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

2. 환경 변수 설정:
```bash
cp .env.example .env
# .env 파일을 편집하여 Azure AD 앱 정보 입력
```

## 사용 방법

### 1. 기본 사용

```python
from auth import AuthService

# 서비스 초기화
auth_service = AuthService()

# 인증 플로우 시작
auth_info = auth_service.start_auth_flow()
print(f"Auth URL: {auth_info['auth_url']}")

# 인증 완료 (콜백에서 받은 코드로)
session = await auth_service.complete_auth_flow(
    authorization_code="received_code",
    state=auth_info['state']
)
print(f"Session ID: {session['session_id']}")
```

### 2. 토큰 갱신

```python
# 자동 토큰 갱신이 포함된 유효한 토큰 가져오기
token = await auth_service.get_valid_token(session_id)
```

### 3. 세션 관리

```python
# 세션 정보 조회
session_info = auth_service.get_session_info(session_id)

# 로그아웃
auth_service.logout(session_id)

# 만료된 세션 정리
cleaned = auth_service.cleanup_expired_sessions()
```

## 환경 변수

- `AZURE_CLIENT_ID`: Azure AD 애플리케이션 ID
- `AZURE_CLIENT_SECRET`: Azure AD 클라이언트 시크릿
- `AZURE_TENANT_ID`: Azure AD 테넌트 ID (기본값: common)
- `AZURE_REDIRECT_URI`: OAuth 콜백 URI
- `DB_PATH`: 데이터베이스 파일 경로
- `LOG_LEVEL`: 로그 레벨 (DEBUG, INFO, WARNING, ERROR)

## 주요 클래스

### AuthService
메인 인증 서비스 클래스로 전체 인증 플로우를 관리합니다.

### AzureConfig
Azure AD 설정 및 앱 정보를 관리합니다.

### OAuthClient
OAuth 2.0 프로토콜 구현 및 Azure AD와의 통신을 담당합니다.

### TokenManager
토큰 및 세션 정보를 데이터베이스에 저장/관리합니다.

## 라이선스

MIT# connector_auth
