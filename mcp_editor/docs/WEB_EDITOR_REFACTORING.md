# MCP 웹에디터 리팩토링 가이드

## ⚠️ 핵심 제약사항

### 절대 준수 사항
1. **UI/UX 완전 보존**: 픽셀 단위까지 현재 디자인 유지
2. **하드코딩 제거 필수**:
   - ❌ 금지: outlook, graph_mail, file_handler 등 특정 서버명
   - ❌ 금지: create_email, send_email 등 특정 함수명
   - ❌ 금지: /home/kimghw/... 등 절대 경로
3. **단계별 검증 필수**: 각 변경 후 즉시 UI/기능 테스트

## 개요

### 프로젝트 현황
- **현재 구조**: 단일 HTML 파일에 모든 코드 포함 (5,143줄)
- **목표**: 모듈화된 구조로 분리하여 유지보수성 향상
- **상태**: 아직 리팩토링 미완료 (단일 파일 상태 유지)

### 리팩토링 목표
1. HTML, CSS, JavaScript를 독립적인 파일로 분리
2. JavaScript 코드를 기능별 모듈로 구분
3. **모든 하드코딩 값 제거 및 동적 로딩 구현**
4. **UI/UX 100% 동일성 보장**
5. 성능 최적화 및 캐싱 가능하도록 구조 개선

---

## 현재 파일 구조 분석

### tool_editor.html (5,143줄)
```
구성 요소:
├── HTML 구조 (약 300줄)
├── CSS 스타일 (약 1,200줄)
└── JavaScript 코드 (약 3,600줄)
```

### 주요 기능 블록
1. **초기화 및 설정**
   - 서버 목록 로딩
   - 툴 목록 초기화
   - 이벤트 리스너 바인딩

2. **UI 렌더링**
   - 서버 드롭다운
   - 툴 목록 사이드바
   - 툴 편집 영역
   - 파라미터 테이블

3. **데이터 처리**
   - API 통신
   - 데이터 검증
   - 상태 관리

4. **코드 생성**
   - Python 코드 생성
   - JSON Schema 생성
   - 서버 템플릿 생성

---

## 제안하는 모듈 구조

### 디렉토리 구조
```
mcp_editor/
├── templates/
│   └── tool_editor.html         # HTML 구조만 포함
├── static/
│   ├── css/
│   │   ├── tool_editor.css     # 메인 스타일
│   │   ├── components.css      # 컴포넌트 스타일
│   │   └── themes.css           # 테마 정의
│   └── js/
│       ├── core.js              # 핵심 기능
│       ├── ui.js                # UI 렌더링
│       ├── actions.js           # 이벤트 처리
│       ├── generator.js         # 코드 생성
│       └── api.js               # API 통신
└── docs/
    └── refactoring/
        ├── guide.md
        └── migration.md
```

---

## 하드코딩 제거 목록

### 제거 대상
| 라인 | 현재 코드 | 변경 방안 |
|------|----------|-----------|
| 1022 | "outlook_types.py" | API에서 타입 소스 동적 로드 |
| 1629 | "/home/kimghw/.../template.jinja2" | 설정 파일 또는 API |
| 1831, 1838 | 'outlook' (기본값) | 서버 목록 첫 번째 사용 |
| 3587, 3712 | "outlook_types.py" | 동적 타입 소스 참조 |

## 단계별 리팩토링 계획

### ⚠️ 각 Phase 시작 전 필수 작업
1. 현재 상태 스크린샷 저장
2. 기능 동작 비디오 녹화
3. HTML 파일 백업 생성

### Phase 1: 기본 분리 (우선순위: 높음)

#### 1-1. CSS 추출
```css
/* static/css/tool_editor.css */
:root {
    --primary-color: #0071e3;
    --primary-hover: #0077ed;
    /* ... CSS 변수 정의 ... */
}

/* 레이아웃 스타일 */
.container { ... }
.sidebar { ... }
.main-content { ... }

/* 컴포넌트 스타일 */
.tool-list { ... }
.parameter-table { ... }
```

**검증 체크리스트:**
- [ ] 색상 동일
- [ ] 레이아웃 동일
- [ ] 폰트 동일
- [ ] 애니메이션 동일
- [ ] 반응형 동작 동일

#### 1-2. JavaScript 모듈 분리
```javascript
// static/js/core.js
const MCPEditor = {
    state: {
        currentServer: null,  // 하드코딩 없음!
        currentTool: null,
        tools: {},
        servers: []  // 동적 로드
    },

    async init() {
        await this.loadConfig();  // 설정 먼저 로드
        await this.loadServers();
        this.bindEvents();
    },

    async loadConfig() {
        // 하드코딩된 값 대신 API에서 로드
        const config = await fetch('/api/config');
        this.config = await config.json();
    }
};

// static/js/api.js
const API = {
    baseURL: '/api',

    async getServers() {
        return fetch(`${this.baseURL}/servers`);
    },

    async saveTool(server, tool, data) {
        return fetch(`${this.baseURL}/servers/${server}/tools/${tool}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }
};
```

**검증 체크리스트:**
- [ ] 서버 선택 동작
- [ ] 툴 로딩 동작
- [ ] 이벤트 핸들링
- [ ] API 통신
- [ ] 하드코딩 값 없음

#### 1-3. HTML 정리
```html
<!-- tool_editor.html -->
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="/static/css/tool_editor.css">
</head>
<body>
    <div class="container">
        <!-- HTML 구조만 유지 -->
    </div>

    <script src="/static/js/core.js"></script>
    <script src="/static/js/api.js"></script>
    <script src="/static/js/ui.js"></script>
    <script src="/static/js/actions.js"></script>
    <script src="/static/js/generator.js"></script>
    <script>
        MCPEditor.init();
    </script>
</body>
</html>
```

### Phase 2: 모듈 시스템 구현 (우선순위: 중간)

#### 2-1. ES6 모듈 전환
```javascript
// core.js
export class MCPEditor {
    constructor() {
        this.state = {};
    }
}

// main.js
import { MCPEditor } from './core.js';
import { API } from './api.js';

const editor = new MCPEditor();
editor.init();
```

#### 2-2. 번들링 설정
```javascript
// webpack.config.js
module.exports = {
    entry: './static/js/main.js',
    output: {
        filename: 'bundle.js',
        path: './static/dist'
    }
};
```

### Phase 3: 컴포넌트화 (우선순위: 낮음)

#### 3-1. UI 컴포넌트 생성
```javascript
// components/ToolList.js
class ToolList {
    constructor(container) {
        this.container = container;
    }

    render(tools) {
        // 툴 목록 렌더링
    }
}

// components/ParameterTable.js
class ParameterTable {
    constructor(container) {
        this.container = container;
    }

    addParameter() {
        // 파라미터 추가
    }
}
```

---

## 마이그레이션 체크리스트

### 기능 테스트
- [ ] 서버 목록 로딩
- [ ] 서버 선택 및 변경
- [ ] 툴 목록 표시
- [ ] 툴 선택 및 상세 표시
- [ ] 파라미터 추가/수정/삭제
- [ ] Internal 토글 기능
- [ ] 툴 저장
- [ ] 서버 코드 생성
- [ ] 모달 다이얼로그
- [ ] 에러 처리 및 알림

### 성능 검증
- [ ] 초기 로딩 시간
- [ ] API 응답 속도
- [ ] UI 렌더링 성능
- [ ] 메모리 사용량

### 브라우저 호환성
- [ ] Chrome/Edge (최신)
- [ ] Firefox (최신)
- [ ] Safari (최신)

---

## 주요 함수 매핑

### 현재 → 리팩토링 후

| 현재 함수 | 새 모듈 | 새 함수명 |
|---------|--------|---------|
| `loadServers()` | `api.js` | `API.getServers()` |
| `renderToolList()` | `ui.js` | `UI.renderToolList()` |
| `handleToolSelect()` | `actions.js` | `Actions.selectTool()` |
| `generateToolDefinition()` | `generator.js` | `Generator.createToolCode()` |
| `saveCurrentTool()` | `core.js` | `MCPEditor.saveTool()` |

---

## 개발 환경 설정

### 개발 서버 실행
```bash
# FastAPI 서버 실행
cd mcp_editor
uvicorn main:app --reload --port 8000

# 정적 파일 서버 (개발용)
python -m http.server 8001
```

### 파일 감시 및 자동 새로고침
```bash
# 파일 변경 감시
npm install -g nodemon
nodemon --watch static --ext js,css,html
```

---

## 트러블슈팅

### 일반적인 문제 해결

#### 스크립트 로딩 순서 문제
```html
<!-- 올바른 순서 -->
<script src="core.js"></script>    <!-- 1. 기본 설정 -->
<script src="api.js"></script>      <!-- 2. API 모듈 -->
<script src="ui.js"></script>       <!-- 3. UI 모듈 -->
<script src="generator.js"></script> <!-- 4. 생성기 -->
<script src="actions.js"></script>  <!-- 5. 액션 핸들러 -->
```

#### 전역 변수 접근 문제
```javascript
// 문제: 모듈 간 변수 공유
// 해결: window 객체 사용 또는 모듈 export/import

// window 객체 사용
window.MCPEditor = {
    state: {},
    methods: {}
};

// 다른 모듈에서 접근
window.MCPEditor.state.currentTool;
```

#### 이벤트 바인딩 문제
```javascript
// 문제: DOM이 준비되기 전 바인딩
// 해결: DOMContentLoaded 이벤트 사용

document.addEventListener('DOMContentLoaded', () => {
    MCPEditor.init();
    bindEventListeners();
});
```

---

## 모범 사례

### 코드 구조화
1. **단일 책임 원칙**: 각 모듈은 하나의 명확한 역할만 담당
2. **느슨한 결합**: 모듈 간 의존성 최소화
3. **명확한 인터페이스**: 공개 API와 내부 구현 분리

### 네이밍 규칙
```javascript
// 상수: UPPER_SNAKE_CASE
const MAX_PARAMETERS = 50;

// 클래스: PascalCase
class ToolEditor {}

// 함수/변수: camelCase
function loadToolDetails() {}
let currentServer = null;

// 프라이빗: 언더스코어 프리픽스
function _validateInput() {}
```

### 에러 처리
```javascript
// API 호출 시 에러 처리
async function loadTools() {
    try {
        const response = await API.getTools();
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Failed to load tools:', error);
        UI.showError('툴 목록을 불러올 수 없습니다.');
        return [];
    }
}
```

---

## 성과 지표

### 개선 목표
- **코드 가독성**: 파일당 최대 500줄
- **로딩 성능**: 초기 로딩 2초 이내
- **유지보수성**: 기능별 독립적 수정 가능
- **테스트 가능성**: 단위 테스트 커버리지 80% 이상

### 측정 방법
```javascript
// 성능 측정
console.time('App Init');
MCPEditor.init().then(() => {
    console.timeEnd('App Init');
});

// 메모리 사용량
console.log('Memory:', performance.memory.usedJSHeapSize / 1048576, 'MB');
```

---

## 참고 자료

### 문서
- [JavaScript 모듈 시스템](https://developer.mozilla.org/ko/docs/Web/JavaScript/Guide/Modules)
- [웹 성능 최적화](https://web.dev/fast/)
- [MCP Protocol Docs](https://modelcontextprotocol.io)

### 도구
- [Webpack](https://webpack.js.org/) - 모듈 번들러
- [ESLint](https://eslint.org/) - 코드 품질 도구
- [Prettier](https://prettier.io/) - 코드 포맷터

---

*작성일: 2025-12-26*
*버전: 1.0.0*