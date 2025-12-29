# 리팩토링 검증 프로토콜

## 개요
이 문서는 MCP 웹에디터 리팩토링 시 UI/UX 일관성을 보장하기 위한 검증 절차를 정의합니다.

---

## 하드코딩 제거 대상 목록

### 1. 서버/프로파일 관련
| 라인 | 현재 코드 | 문제점 | 해결 방안 |
|------|----------|--------|-----------|
| 1831 | `currentProfile \|\| 'outlook'` | outlook 하드코딩 | `currentProfile \|\| servers[0]` |
| 1838 | `currentProfile \|\| 'outlook'` | outlook 하드코딩 | `currentProfile \|\| servers[0]` |

### 2. 파일/경로 관련
| 라인 | 현재 코드 | 문제점 | 해결 방안 |
|------|----------|--------|-----------|
| 1022 | "outlook_types.py" | 파일명 하드코딩 | API에서 타입 소스 동적 로드 |
| 1629 | `/home/kimghw/.../template.jinja2` | 절대 경로 하드코딩 | 설정 파일 또는 API 제공 |
| 3587 | "outlook_types.py" | 파일명 하드코딩 | 동적 타입 소스 참조 |
| 3712 | "outlook_types.py" | 파일명 하드코딩 | 동적 타입 소스 참조 |

### 3. 제거 대상 문자열 패턴
```javascript
// 금지된 하드코딩 패턴
const FORBIDDEN_PATTERNS = [
    /outlook|graph_mail|file_handler/i,  // 특정 서버명
    /create_email|send_email|get_emails/i,  // 특정 함수명
    /\/home\/\w+\//,  // 절대 경로
    /outlook_types\.py/,  // 특정 파일명
];
```

---

## 단계별 검증 체크리스트

### 🔍 Phase 0: 현재 상태 기록

#### UI 스냅샷 생성
```bash
# 1. 서버 실행 상태에서 스크린샷
# 2. 각 기능별 상태 캡처
mkdir -p docs/screenshots/original
```

- [ ] 메인 화면 (툴 목록 표시)
- [ ] 툴 선택 상태
- [ ] 파라미터 편집 상태
- [ ] 모달 열린 상태
- [ ] 에러 메시지 표시 상태

#### 기능 동작 기록
- [ ] 서버 드롭다운 옵션 목록
- [ ] 툴 목록 정렬 순서
- [ ] 버튼 클릭 응답 시간
- [ ] API 호출 순서

---

### ✅ Phase 1: CSS 분리 검증

#### 작업 전
- [ ] HTML 파일 백업
- [ ] 브라우저 개발자 도구로 Computed Styles 저장
- [ ] CSS 애니메이션 목록 작성

#### 작업 중
```html
<!-- Before -->
<style>
    /* 모든 스타일 */
</style>

<!-- After -->
<link rel="stylesheet" href="/static/css/tool_editor.css">
```

#### 작업 후 검증
- [ ] **레이아웃**: Flexbox/Grid 정렬 동일
- [ ] **색상**: CSS 변수 값 동일
- [ ] **폰트**: 크기, 굵기, 간격 동일
- [ ] **간격**: padding, margin 동일
- [ ] **그림자**: box-shadow 효과 동일
- [ ] **애니메이션**: 트랜지션 동작 동일
- [ ] **반응형**: 브레이크포인트 동작 동일

#### 검증 도구
```javascript
// CSS 비교 스크립트
function compareCSSProperties(selector) {
    const original = getComputedStyle(document.querySelector(selector));
    // 리팩토링 후 실행
    const refactored = getComputedStyle(document.querySelector(selector));

    const differences = [];
    for (let prop of original) {
        if (original[prop] !== refactored[prop]) {
            differences.push({
                property: prop,
                original: original[prop],
                refactored: refactored[prop]
            });
        }
    }
    return differences;
}
```

---

### ✅ Phase 2: JavaScript 모듈화 검증

#### 작업 전
- [ ] 전역 변수 목록 (`window.*`)
- [ ] 이벤트 리스너 매핑
- [ ] 함수 호출 체인

#### 작업 중
```javascript
// 모듈 분리 시 주의사항
// 1. 실행 순서 유지
// 2. 전역 접근성 보장
// 3. 이벤트 바인딩 시점
```

#### 작업 후 검증

##### 기능별 테스트
- [ ] **서버 선택**
  - [ ] 드롭다운 옵션 로드
  - [ ] 선택 시 툴 목록 갱신
  - [ ] 현재 선택 상태 표시

- [ ] **툴 관리**
  - [ ] 툴 목록 표시
  - [ ] 툴 선택 하이라이트
  - [ ] 툴 상세 정보 로드
  - [ ] 툴 생성
  - [ ] 툴 삭제

- [ ] **파라미터 편집**
  - [ ] 파라미터 추가
  - [ ] 파라미터 삭제
  - [ ] 타입 변경
  - [ ] Required 토글
  - [ ] Enum 값 입력

- [ ] **저장/생성**
  - [ ] Save 버튼 동작
  - [ ] Generate Server 모달
  - [ ] 프로토콜 선택
  - [ ] 코드 생성

##### 콘솔 체크
- [ ] 에러 없음
- [ ] 경고 없음
- [ ] 네트워크 요청 정상

---

### ✅ Phase 3: 하드코딩 제거 검증

#### 작업 전
- [ ] 하드코딩된 값 사용 위치 모두 표시
- [ ] 대체 값 소스 확인 (API/설정)

#### 작업 중
```javascript
// 하드코딩 제거 패턴
// Before
const server = currentProfile || 'outlook';

// After
const server = currentProfile || await getDefaultServer();

// 설정 로더 추가
async function loadAppConfig() {
    const config = await fetch('/api/config');
    return config.json();
}
```

#### 작업 후 검증
- [ ] **동적 로딩 확인**
  - [ ] 서버 목록 API에서 로드
  - [ ] 기본 서버 자동 선택
  - [ ] 타입 소스 동적 참조

- [ ] **하드코딩 검색**
  ```bash
  # 금지된 문자열 검색
  grep -i "outlook\|graph_mail" tool_editor.html
  grep "outlook_types\.py" tool_editor.html
  grep "/home/" tool_editor.html
  ```

- [ ] **경로 독립성**
  - [ ] 상대 경로 사용
  - [ ] 환경 변수 활용
  - [ ] 설정 파일 기반

---

### ✅ Phase 4: 통합 검증

#### 시각적 회귀 테스트
```javascript
// 픽셀 비교 테스트
async function visualRegressionTest() {
    const pages = [
        '/',
        '/?server=test',
        '/?server=test&tool=sample'
    ];

    for (const page of pages) {
        const original = await captureScreenshot(`original${page}`);
        const current = await captureScreenshot(`current${page}`);

        const diff = await compareImages(original, current);
        if (diff > 0) {
            console.error(`Visual regression on ${page}: ${diff} pixels`);
        }
    }
}
```

#### 성능 비교
- [ ] 초기 로딩 시간 (< 2초)
- [ ] API 응답 시간 (< 500ms)
- [ ] UI 반응 시간 (< 100ms)

#### E2E 시나리오
```javascript
// 전체 워크플로우 테스트
async function e2eTest() {
    // 1. 페이지 로드
    await page.goto('/');

    // 2. 서버 선택
    await page.select('#server-select', 'test-server');

    // 3. 툴 선택
    await page.click('.tool-item:first-child');

    // 4. 파라미터 추가
    await page.click('#add-param-btn');

    // 5. 저장
    await page.click('#save-btn');

    // 검증
    const notification = await page.$('.notification.success');
    assert(notification !== null);
}
```

---

## 검증 결과 기록

### 템플릿
```markdown
## 검증 일자: YYYY-MM-DD

### Phase: [1/2/3/4]

#### 작업 내용
-

#### 검증 결과
- [ ] UI 동일성: [PASS/FAIL]
- [ ] 기능 동작: [PASS/FAIL]
- [ ] 성능: [PASS/FAIL]

#### 발견된 이슈
1.
2.

#### 해결 방법
1.
2.

#### 스크린샷
- Before: [링크]
- After: [링크]
- Diff: [링크]
```

---

## 롤백 프로토콜

### 롤백 트리거
1. UI가 1px 이상 차이
2. 기능 하나라도 미동작
3. 콘솔 에러 발생
4. API 호환성 깨짐

### 롤백 절차
```bash
# 1. 즉시 중단
ctrl+c

# 2. Git 롤백
git checkout -- .

# 3. 백업 복원
cp backups/tool_editor.html.$(date +%Y%m%d) templates/tool_editor.html

# 4. 서버 재시작
pkill -f "python.*8000"
python main.py
```

---

## 자동화 스크립트

### 검증 자동화
```bash
#!/bin/bash
# validation.sh

echo "=== MCP Editor Refactoring Validation ==="

# 1. 하드코딩 검사
echo "Checking hardcoded values..."
if grep -q "outlook\|graph_mail" templates/tool_editor.html; then
    echo "❌ Hardcoded server names found!"
    exit 1
fi

# 2. 파일 구조 검사
echo "Checking file structure..."
required_files=(
    "static/css/tool_editor.css"
    "static/js/core.js"
    "static/js/ui.js"
    "static/js/actions.js"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing: $file"
        exit 1
    fi
done

# 3. 서버 테스트
echo "Testing server..."
curl -s http://localhost:8000/api/servers > /dev/null
if [ $? -ne 0 ]; then
    echo "❌ Server not responding"
    exit 1
fi

echo "✅ All validations passed!"
```

---

## 성공 기준

### 필수 요구사항
1. **UI 100% 동일**: 픽셀 단위 일치
2. **기능 100% 동작**: 모든 테스트 통과
3. **하드코딩 0%**: 동적 로딩 완료
4. **성능 저하 없음**: 기존 대비 동등 이상

### 품질 지표
- 코드 라인 수: 30% 감소
- 파일 크기: 모듈별 500줄 이하
- 로딩 시간: 2초 이내
- 응답 시간: 100ms 이내

---

*버전: 1.0.0*
*작성일: 2025-12-26*
*검증 책임자: 개발팀*