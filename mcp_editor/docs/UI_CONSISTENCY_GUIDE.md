# UI 일관성 유지 가이드

## 핵심 원칙

### 1. UI/UX 불변 원칙
- **절대 불변**: 현재 tool_editor.html의 모든 시각적 요소와 사용자 경험 유지
- **레이아웃 보존**: 사이드바, 헤더, 메인 컨텐츠 영역 구조 그대로 유지
- **스타일 보존**: 색상, 폰트, 간격, 애니메이션 완전 동일

### 2. 하드코딩 제거 원칙
- **금지 항목**:
  - 특정 서버명 하드코딩 (outlook, graph_mail 등)
  - 특정 함수명 하드코딩 (create_email, send_email 등)
  - 특정 경로 하드코딩 (/home/kimghw/... 등)
- **동적 로딩**: 모든 데이터는 API를 통해 동적으로 로드

### 3. 단계별 검증 원칙
- **각 변경 후 즉시 테스트**
- **UI 스크린샷 비교**
- **기능 동작 검증**

---

## 현재 UI 구조 (보존 대상)

### 레이아웃
```
┌──────────────────────────────────────────┐
│                 Header                    │
│  - Title: "MCP Tool Definitions Editor"   │
│  - Server Selector Dropdown               │
├────────────┬─────────────────────────────┤
│            │                             │
│  Sidebar   │      Main Content          │
│            │                             │
│  Tool List │   Tool Editor Form         │
│            │   - Description             │
│            │   - Internal Toggle         │
│            │   - Parameters Table        │
│            │   - Action Buttons          │
│            │                             │
└────────────┴─────────────────────────────┘
```

### 주요 UI 컴포넌트

#### 1. 헤더 (Header)
- 타이틀: "MCP Tool Definitions Editor"
- 그라데이션 텍스트 효과
- 서버 선택 드롭다운

#### 2. 사이드바 (Sidebar)
- 툴 목록
- 검색 기능
- 선택된 툴 하이라이트
- 툴 개수 표시

#### 3. 메인 편집 영역
- 툴 설명 입력
- Internal 체크박스
- 파라미터 테이블
  - Name, Type, Description, Required, Enum Values, Actions
  - Add Parameter 버튼
  - Delete 버튼 (각 행)
- Save, Delete Tool, Generate Server 버튼

#### 4. 모달 다이얼로그
- 서버 생성 모달
- 확인 다이얼로그
- 알림 메시지

### 스타일 요소 (CSS Variables)
```css
:root {
    --primary-color: #0071e3;
    --primary-hover: #0077ed;
    --danger-color: #ff3b30;
    --danger-hover: #ff453a;
    --success-color: #34c759;
    --warning-color: #ff9f0a;
    --bg-color: #f5f5f7;
    --card-bg: #ffffff;
    --sidebar-bg: #ffffff;
    --border-color: #d2d2d7;
    --text-primary: #1d1d1f;
    --text-secondary: #86868b;
}
```

---

## 하드코딩 제거 대상

### 현재 하드코딩된 값들

| 위치 | 하드코딩된 값 | 변경 방안 |
|------|--------------|-----------|
| Line 1022 | "outlook_types.py" | API에서 동적 로드 |
| Line 1831 | 'outlook' (기본값) | 서버 목록 첫 번째 항목 사용 |
| Line 1629 | '/home/kimghw/...' 경로 | 상대 경로 또는 설정 파일 |
| Line 3587 | "outlook_types.py" | 동적 타입 소스 참조 |

### 제거 방법
```javascript
// Before (하드코딩)
const serverName = currentProfile || 'outlook';

// After (동적)
const serverName = currentProfile || servers[0] || '';

// Before (하드코딩된 경로)
templateInput.value = '/home/kimghw/Connector_auth/jinja/...';

// After (설정 기반)
templateInput.value = config.template_path || '';
```

---

## 단계별 리팩토링 및 검증

### Phase 1: CSS 추출 (UI 영향도: 무)

#### 작업 전 체크리스트
- [ ] 현재 페이지 스크린샷 저장
- [ ] 모든 상호작용 요소 목록 작성
- [ ] 애니메이션/트랜지션 목록 작성

#### CSS 추출 작업
```bash
# 1. CSS 추출
- <style> 태그 내용을 tool_editor.css로 이동
- 순서 그대로 유지 (중요!)
- 주석 포함 모두 복사
```

#### 작업 후 검증
- [ ] 스크린샷 픽셀 단위 비교
- [ ] 호버 효과 동작 확인
- [ ] 반응형 레이아웃 테스트
- [ ] 애니메이션 동작 확인

### Phase 2: JavaScript 함수 분리 (UI 영향도: 낮음)

#### 작업 전 체크리스트
- [ ] 모든 이벤트 핸들러 목록
- [ ] 전역 변수 목록
- [ ] DOM 조작 함수 목록

#### JavaScript 모듈화
```javascript
// 1. 전역 상태 (core.js)
window.MCPEditorState = {
    currentServer: null,
    currentTool: null,
    tools: {},
    servers: []
};

// 2. 기존 함수 래핑 (호환성 유지)
window.loadServers = function() {
    // 기존 코드 그대로
};
```

#### 작업 후 검증
- [ ] 서버 드롭다운 동작
- [ ] 툴 선택 동작
- [ ] 파라미터 추가/삭제
- [ ] 저장 기능
- [ ] 모달 표시/숨김

### Phase 3: 하드코딩 제거 (UI 영향도: 무)

#### 작업 전 백업
```bash
# 백업 생성
cp tool_editor.html tool_editor.html.backup
```

#### 동적 값 교체
```javascript
// 설정 객체 생성
const AppConfig = {
    defaults: {
        server: null,  // 첫 번째 서버 자동 선택
        template_path: null  // API에서 로드
    },

    types: {
        source: null  // "outlook_types.py" 대신 동적
    }
};

// 초기화 시 설정 로드
async function loadConfig() {
    const config = await fetch('/api/config').then(r => r.json());
    Object.assign(AppConfig, config);
}
```

#### 작업 후 검증
- [ ] 서버 자동 선택 동작
- [ ] 타입 선택 동작
- [ ] 경로 자동 완성
- [ ] 에러 메시지 표시

### Phase 4: 통합 테스트

#### 전체 기능 테스트
- [ ] 서버 목록 로딩
- [ ] 서버 선택 변경
- [ ] 툴 목록 표시
- [ ] 툴 생성
- [ ] 툴 편집
- [ ] 툴 삭제
- [ ] 파라미터 관리
- [ ] 서버 코드 생성
- [ ] 데이터 저장

#### UI 일관성 최종 확인
- [ ] 원본과 비교 (스크린샷)
- [ ] 색상/스타일 동일
- [ ] 레이아웃 동일
- [ ] 상호작용 동일

---

## 검증 도구

### 스크린샷 비교
```javascript
// 자동 스크린샷 비교 스크립트
async function compareUI() {
    const original = await captureScreenshot('original.html');
    const refactored = await captureScreenshot('refactored.html');

    const diff = pixelmatch(original, refactored, null,
        width, height, {threshold: 0.1});

    console.log(`Pixel difference: ${diff}`);
    return diff === 0;
}
```

### DOM 구조 비교
```javascript
// DOM 구조 검증
function compareDOM() {
    const originalDOM = document.querySelector('.container').innerHTML;
    const refactoredDOM = /* 리팩토링 후 DOM */;

    return originalDOM === refactoredDOM;
}
```

### 이벤트 리스너 검증
```javascript
// 이벤트 리스너 확인
function verifyEventListeners() {
    const elements = [
        '#server-select',
        '.tool-item',
        '#save-btn',
        '#add-param-btn'
    ];

    elements.forEach(selector => {
        const el = document.querySelector(selector);
        const listeners = getEventListeners(el);
        console.log(`${selector}: ${listeners}`);
    });
}
```

---

## 롤백 계획

### 즉시 롤백 조건
1. UI가 시각적으로 변경됨
2. 기능이 작동하지 않음
3. 콘솔 에러 발생

### 롤백 절차
```bash
# 1. 현재 변경사항 저장
git stash

# 2. 이전 커밋으로 롤백
git checkout HEAD~1

# 3. 또는 백업 파일 복원
cp tool_editor.html.backup tool_editor.html
```

---

## 체크포인트

### 각 단계 완료 기준
1. **CSS 추출**: 픽셀 단위 동일한 렌더링
2. **JS 모듈화**: 모든 기능 정상 동작
3. **하드코딩 제거**: 동적 로딩 확인
4. **최종 검증**: 100% 기능 및 UI 일치

### 문서화 요구사항
- 변경 전후 스크린샷
- 테스트 결과 로그
- 성능 측정 데이터
- 발견된 이슈 및 해결 방법

---

*작성일: 2025-12-26*
*중요도: 최우선*