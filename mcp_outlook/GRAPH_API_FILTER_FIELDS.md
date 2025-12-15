# Microsoft Graph API 메일 조회 파라미터 설명서

## 목차
1. [개요](#개요)
2. [$filter 파라미터](#filter-파라미터)
3. [$select 파라미터](#select-파라미터)
4. [$search 파라미터](#search-파라미터)
5. [기타 쿼리 파라미터](#기타-쿼리-파라미터)
6. [API 응답 형태](#api-응답-형태)
7. [사용 예시](#사용-예시)

---

## 개요

Microsoft Graph API를 통해 Outlook 메일을 조회할 때 사용하는 주요 OData 쿼리 파라미터는 `$filter`, `$select`, `$search`입니다. 이 파라미터들을 통해 필요한 메일만 필터링하고, 원하는 필드만 선택하여 효율적인 데이터 조회가 가능합니다.

### 기본 엔드포인트

#### 1. `/me/messages`
```
https://graph.microsoft.com/v1.0/me/messages
```
- **현재 인증된 사용자의 메일만 조회**
- `me`는 Authorization 헤더의 Access Token에서 자동으로 사용자 식별
- 가장 일반적으로 사용되는 엔드포인트

#### 2. `/users/{user-id}/messages`
```
https://graph.microsoft.com/v1.0/users/{user-id}/messages
https://graph.microsoft.com/v1.0/users/john@company.com/messages
https://graph.microsoft.com/v1.0/users/48d31887-5fad-4d73-a9f5-3c356e68a038/messages
```
- **다른 사용자의 메일 조회 가능** (적절한 권한 필요)
- 주로 관리자나 위임된 권한을 가진 애플리케이션에서 사용
- 필요 권한:
  - **Delegated**: `Mail.Read.Shared` (공유 메일함) 또는 `Mail.Read` (본인)
  - **Application**: `Mail.Read` (모든 사용자 - 관리자 동의 필요)

### 인증 방식
Access Token은 Authorization 헤더에 포함되며, 토큰 내부에 사용자 정보가 인코딩되어 있습니다:
```
Authorization: Bearer {access_token}
```

토큰에 포함된 주요 정보:
- `upn` 또는 `preferred_username`: 사용자 이메일
- `oid`: 사용자 객체 ID
- `scp`: 부여된 권한 스코프

---

## $filter 파라미터

### 개념
`$filter`는 특정 조건을 만족하는 메일만 조회하기 위한 필터링 파라미터입니다.

### 지원 연산자
- **비교 연산자**: `eq` (같음), `ne` (같지 않음), `gt` (보다 큼), `ge` (크거나 같음), `lt` (보다 작음), `le` (작거나 같음)
- **논리 연산자**: `and`, `or`, `not`
- **문자열 함수**: `contains()`, `startswith()`, `endswith()`
- **컬렉션 함수**: `any()` (배열 필드용)

### 주요 필터 가능 필드

#### 1. 발신자 관련
```
from/emailAddress/address eq 'sender@example.com'
sender/emailAddress/address eq 'sender@example.com'
```

#### 2. 날짜/시간 관련
```
receivedDateTime ge 2024-12-01T00:00:00Z
sentDateTime le 2024-12-07T23:59:59Z
createdDateTime gt 2024-11-30T00:00:00Z
lastModifiedDateTime ge 2024-12-01T00:00:00Z
```

#### 3. 메일 상태
```
isRead eq false                    # 읽지 않은 메일
isDraft eq false                    # 임시저장이 아닌 메일
hasAttachments eq true              # 첨부파일이 있는 메일
isDeliveryReceiptRequested eq true # 배달 확인 요청
isReadReceiptRequested eq true     # 읽음 확인 요청
```

#### 4. 메일 속성
```
importance eq 'high'                # 중요도 (low, normal, high)
sensitivity eq 'confidential'       # 민감도 (normal, personal, private, confidential)
inferenceClassification eq 'focused' # AI 분류 (focused, other)
```

#### 5. 내용 검색
```
contains(subject, '회의')           # 제목에 '회의' 포함
contains(body/content, '프로젝트')  # 본문에 '프로젝트' 포함
contains(bodyPreview, '안내')       # 미리보기에 '안내' 포함
```

#### 6. ID 관련
```
id eq 'AAMkAGI2TG93AAA='           # 특정 메일 ID
conversationId eq 'AAQkAGI2AAA='   # 대화 스레드 ID
parentFolderId eq 'AAMkAGI2TAAAA=' # 폴더 ID
```

#### 7. 카테고리 및 플래그
```
categories/any(c:c eq 'Important')  # 특정 카테고리
flag/flagStatus eq 'flagged'        # 플래그 상태 (notFlagged, complete, flagged)
```

### 복합 필터 예시
```
# 최근 3일간 받은 읽지 않은 중요 메일
receivedDateTime ge 2024-12-04T00:00:00Z and isRead eq false and importance eq 'high'

# 특정 발신자 제외
receivedDateTime ge 2024-12-01T00:00:00Z and from/emailAddress/address ne 'noreply@github.com'

# 여러 조건 조합
(from/emailAddress/address eq 'boss@company.com' or importance eq 'high') and hasAttachments eq true
```

---

## $select 파라미터

### 개념
`$select`는 응답에 포함할 필드를 명시적으로 지정하여 불필요한 데이터 전송을 줄입니다.

### 선택 가능한 주요 필드

#### 기본 정보
- `id`: 메일 고유 ID
- `createdDateTime`: 생성 시각
- `lastModifiedDateTime`: 최종 수정 시각
- `changeKey`: 버전 관리 키

#### 메일 메타데이터
- `subject`: 제목
- `bodyPreview`: 본문 미리보기 (255자)
- `importance`: 중요도
- `sensitivity`: 민감도
- `categories`: 카테고리 목록
- `conversationId`: 대화 스레드 ID
- `conversationIndex`: 대화 내 순서

#### 날짜/시간
- `receivedDateTime`: 수신 시각
- `sentDateTime`: 발송 시각

#### 상태 정보
- `isRead`: 읽음 여부
- `isDraft`: 임시저장 여부
- `hasAttachments`: 첨부파일 유무
- `isDeliveryReceiptRequested`: 배달 확인 요청
- `isReadReceiptRequested`: 읽음 확인 요청

#### 복합 객체 (중첩 구조)
- `body`: 본문 전체 (contentType, content)
- `from`: 발신자 (emailAddress.name, emailAddress.address)
- `sender`: 실제 발송자
- `toRecipients`: 수신자 목록
- `ccRecipients`: 참조 목록
- `bccRecipients`: 숨은 참조 목록
- `replyTo`: 회신 주소
- `flag`: 플래그 정보 (flagStatus)

### 사용 예시
```
# 기본 필드만 선택
$select=id,subject,from,receivedDateTime

# 복합 객체 포함
$select=id,subject,from,body,toRecipients,hasAttachments

# 최소 필드만
$select=id,subject,bodyPreview
```

---

## $search 파라미터

### 개념
`$search`는 메일 전체를 대상으로 키워드 검색을 수행합니다.

### 특징
- **전체 텍스트 검색**: 제목, 본문, 발신자 등 모든 텍스트 필드 검색
- **KQL(Keyword Query Language)** 지원
- ⚠️ **$filter와 동시 사용 불가**

### 검색 구문
```
# 단순 키워드 검색
$search="프로젝트"

# 구문 검색 (정확한 일치)
$search="\"월간 보고서\""

# AND 연산
$search="프로젝트 AND 회의"

# OR 연산
$search="긴급 OR urgent"

# 특정 필드 검색
$search="from:boss@company.com"
$search="subject:회의"
$search="hasAttachment:true"
```

### KQL 검색 예시
```
# 발신자와 제목 조합
$search="from:manager@company.com AND subject:승인"

# 날짜 범위
$search="received>=2024-12-01 AND received<=2024-12-07"

# 첨부파일이 있는 중요 메일
$search="hasAttachment:true AND importance:high"
```

---

## 기타 쿼리 파라미터

### $top
결과 개수 제한 (최대 1000)
```
$top=50
```

### $skip
페이징을 위한 건너뛰기
```
$skip=100
```

### $orderby
정렬 기준 지정
```
$orderby=receivedDateTime desc
$orderby=subject asc
```

### $count
총 결과 개수 포함
```
$count=true
```

### 조합 예시
```
?$filter=isRead eq false&$select=id,subject,from&$orderby=receivedDateTime desc&$top=20
```

---

## API 응답 형태

### 기본 응답 구조
```json
{
  "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#users('user%40example.com')/messages",
  "@odata.nextLink": "https://graph.microsoft.com/v1.0/users/user@example.com/messages?$skip=10",
  "value": [
    {
      // 메일 객체
    }
  ]
}
```

### 단일 메일 객체 예시
```json
{
  "id": "AAMkAGI2TG93AAA=",
  "createdDateTime": "2024-12-07T10:30:00Z",
  "lastModifiedDateTime": "2024-12-07T10:30:00Z",
  "changeKey": "CQAAABYAAADHcgC8Hl9tRZ",
  "categories": ["Important", "Project"],
  "receivedDateTime": "2024-12-07T10:30:00Z",
  "sentDateTime": "2024-12-07T10:29:45Z",
  "hasAttachments": true,
  "internetMessageId": "<message-id@example.com>",
  "subject": "프로젝트 진행 상황 보고",
  "bodyPreview": "안녕하세요, 12월 프로젝트 진행 상황을 보고드립니다...",
  "importance": "high",
  "parentFolderId": "AAMkAGI2TAAAA=",
  "conversationId": "AAQkAGI2AAA=",
  "conversationIndex": "AQHaH5qAAA==",
  "isDeliveryReceiptRequested": false,
  "isReadReceiptRequested": true,
  "isRead": false,
  "isDraft": false,
  "webLink": "https://outlook.office365.com/owa/?ItemID=AAMkAGI2TG93AAA%3D",
  "inferenceClassification": "focused",
  "body": {
    "contentType": "html",
    "content": "<html><body><p>안녕하세요,</p><p>12월 프로젝트 진행 상황을 보고드립니다...</p></body></html>"
  },
  "sender": {
    "emailAddress": {
      "name": "김철수",
      "address": "kim@company.com"
    }
  },
  "from": {
    "emailAddress": {
      "name": "김철수",
      "address": "kim@company.com"
    }
  },
  "toRecipients": [
    {
      "emailAddress": {
        "name": "이영희",
        "address": "lee@company.com"
      }
    }
  ],
  "ccRecipients": [
    {
      "emailAddress": {
        "name": "박민수",
        "address": "park@company.com"
      }
    }
  ],
  "bccRecipients": [],
  "replyTo": [],
  "flag": {
    "flagStatus": "notFlagged"
  }
}
```

### $count=true 사용 시 응답
```json
{
  "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#users('user%40example.com')/messages",
  "@odata.count": 150,
  "value": [
    // 메일 객체들
  ]
}
```

### 페이징 처리
```json
{
  "@odata.context": "...",
  "@odata.nextLink": "https://graph.microsoft.com/v1.0/users/user@example.com/messages?$skip=100&$top=100",
  "value": [
    // 현재 페이지의 메일들
  ]
}
```

---

## 사용 예시

### Python 코드 예시

#### 1. 필터와 선택 조합
```python
# 최근 7일간 받은 중요 메일만 조회
from datetime import datetime, timedelta, timezone

date_from = (datetime.now(timezone.utc) - timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ')

filter_query = f"receivedDateTime ge {date_from} and importance eq 'high'"
select_fields = "id,subject,from,receivedDateTime,bodyPreview"

url = f"https://graph.microsoft.com/v1.0/me/messages?$filter={filter_query}&$select={select_fields}&$orderby=receivedDateTime desc&$top=50"
```

#### 2. 특정 발신자 제외
```python
# GitHub 알림 메일 제외
filter_query = "receivedDateTime ge 2024-12-01T00:00:00Z and from/emailAddress/address ne 'notifications@github.com'"
```

#### 3. 검색 사용
```python
# "계약서" 키워드가 포함된 메일 검색
search_query = '"계약서"'
select_fields = "id,subject,from,receivedDateTime,hasAttachments"

url = f'https://graph.microsoft.com/v1.0/me/messages?$search="{search_query}"&$select={select_fields}&$top=20'
```

#### 4. 복합 조건
```python
# 읽지 않은 메일 중 첨부파일이 있고 특정 카테고리에 속한 메일
filter_query = "isRead eq false and hasAttachments eq true and categories/any(c:c eq 'Important')"
```

### 실제 구현 예시
```python
import aiohttp
import asyncio

async def query_emails(access_token, filter_params=None, select_fields=None, search_term=None):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    base_url = "https://graph.microsoft.com/v1.0/me/messages"
    params = []

    if filter_params:
        params.append(f"$filter={filter_params}")

    if select_fields:
        params.append(f"$select={','.join(select_fields)}")

    if search_term:
        params.append(f'$search="{search_term}"')

    params.append("$orderby=receivedDateTime desc")
    params.append("$top=50")

    url = f"{base_url}?{'&'.join(params)}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return data.get('value', [])
            else:
                error = await response.text()
                raise Exception(f"API Error: {response.status} - {error}")
```

---

## 주의사항

1. **$filter와 $search는 동시 사용 불가**
   - 둘 중 하나만 선택하여 사용

2. **날짜 형식은 ISO 8601 표준 준수**
   - 예: `2024-12-07T10:30:00Z`

3. **문자열 값은 작은따옴표로 감싸기**
   - 예: `from/emailAddress/address eq 'user@example.com'`

4. **URL 인코딩 필요**
   - 특수문자와 공백은 URL 인코딩 처리

5. **성능 최적화**
   - 필요한 필드만 $select로 지정
   - 적절한 $top 값 설정
   - 인덱싱된 필드 우선 사용

6. **API 제한사항**
   - 단일 요청 최대 1000개 결과
   - 페이징을 통해 추가 데이터 조회
   - Rate limiting 고려

---

## 참고 자료
- [Microsoft Graph API 문서](https://docs.microsoft.com/en-us/graph/api/resources/message)
- [OData 쿼리 파라미터](https://docs.microsoft.com/en-us/graph/query-parameters)
- [KQL 구문 참조](https://docs.microsoft.com/en-us/sharepoint/dev/general-development/keyword-query-language-kql-syntax-reference)