# MCP 웹 에디터 워크플로우 요약

## 전체 흐름

```
서비스 정의 → 스캔 → registry/types JSON 생성 → 웹 에디터 UI
```

---

## 새 프로젝트 설정 순서

### Step 1. 서비스에 데코레이터 추가 (핵심!)

**Python:**
```python
@mcp_service(
    tool_name="handler_xxx",
    server_name="새서버명",      # ← 이것만 지정하면 나머지 자동
    service_name="xxx_service",
    description="설명"
)
def my_service(...):
    ...
```

**JavaScript (TypeScript 권장):**
```typescript
@McpService({
    serverName: "새서버명",
    toolName: "handler_xxx",
    description: "설명"
})
async myService(...) { }
```

### Step 2. 웹 에디터 시작 (자동 처리)

```bash
cd mcp_editor
python app.py
```

자동으로 생성:
- `registry_{server}.json` - 서비스 메타데이터
- `types_property_{server}.json` - 타입 정의
- `editor_config.json` - 프로필 설정

### Step 3. 웹 에디터에서 도구 편집

```
브라우저 → http://localhost:5001
→ 프로필 선택 (새서버명)
→ 서비스 목록 확인
→ 도구 정의 편집/저장
```

### 요약 테이블

| 순서 | 작업 | 수동/자동 |
|------|------|----------|
| 1 | **`@mcp_service(server_name="xxx")` 추가** | 수동 |
| 2 | 웹 에디터 시작 | 자동 스캔 |
| 3 | UI에서 도구 편집 | 수동 |

> **핵심**: `server_name`만 지정하면 나머지는 자동!

---

## 지원 언어

| 언어 | 서비스 정의 방식 | 타입 정의 |
|------|-----------------|----------|
| **Python** | `@mcp_service` 데코레이터 | BaseModel/dataclass |
| **JavaScript** | `server.tool()` 패턴 | Zod 스키마 + Sequelize 모델 |

---

## 1. 서비스 정의 패턴

### Python - 데코레이터 방식 (decorator.md)

```python
@mcp_service(
    tool_name="handler_mail_list",
    server_name="outlook",        # ← 핵심 필드
    service_name="query_mail_list",
    description="메일 리스트 조회"
)
def query_mail_list(self, ...):
    ...
```

### JavaScript - server.tool() 방식

```javascript
server.tool(
    'search_ships',                           // tool_name
    '선박을 검색합니다.',                       // description
    {                                          // Zod 스키마 (파라미터)
        name: z.string().optional().describe('선박 이름'),
        imo: z.string().optional().describe('IMO 번호'),
        shipType: z.enum(['tanker', 'cargo']).optional()
    },
    async (args) => { ... }                   // handler
);
```

**흐름**:
```
Python:     @mcp_service → mcp_service_scanner.py → registry_{server}.json
JavaScript: server.tool() → mcp_service_scanner.py → registry_{server}.json
```

---

## 2. editor_config.json (editor_config.md)

**역할**: 프로필별 경로/포트 설정

**자동 생성**: 웹 에디터 시작 시 `generate_editor_config.py` 자동 실행

**흐름**:
```
@mcp_service(server_name="outlook") → 스캔 → editor_config.json 자동 생성
```

**구조 예시**:
```json
{
  "outlook": {
    "tool_definitions_path": "../mcp_outlook/mcp_server/tool_definitions.py",
    "port": 8001
  }
}
```

---

## 3. 타입 추출 (extract_types.md)

**역할**: 서비스 파라미터의 커스텀 클래스/모델 프로퍼티 자동 추출

### Python
```
서비스 파라미터 (type:"object") → import 추적 → BaseModel 클래스 → 프로퍼티 추출
```

### JavaScript
```
sequelize.define() → Sequelize 모델 스캔 → DataTypes 필드 추출
```

**출력**: `types_property_{server}.json`

**특징**:
- Python: import 경로 자동 추적
- JavaScript: models 디렉토리 자동 스캔

---

## 4. 레지스트리 서버 (registry_server.md)

**역할**: 서비스 메타데이터 저장소

**생성**: `mcp_service_scanner.py` → `registry_{server}.json`

**구조**:
```json
{
  "services": {
    "query_mail_list": {
      "handler": { "class_name": "...", "method": "..." },
      "parameters": [...],
      "metadata": { "tool_name": "...", "description": "..." }
    }
  }
}
```

**API**: `GET /api/mcp-services`, `GET /api/registry`

---

## 통합 데이터 흐름

### Python 프로젝트

```
[소스 코드]
@mcp_service 데코레이터
        │
        ▼
[웹 에디터 시작]
app.py → scan_all_registries()
        │
        ├─→ registry_{server}.json (서비스 + 파라미터)
        ├─→ types_property_{server}.json (BaseModel 타입)
        └─→ editor_config.json (프로필 설정)
                │
                ▼
[웹 에디터 UI]
프로필 선택 → 서비스 목록 → 도구 편집
```

### JavaScript 프로젝트

```
[소스 코드]
server.tool('name', 'desc', zodSchema, handler)
sequelize.define('Model', { fields })
        │
        ▼
[웹 에디터 시작]
app.py → scan_all_registries()
        │
        ├─→ registry_{server}.json (서비스 + Zod 파라미터)
        ├─→ types_property_{server}.json (Sequelize 모델)
        └─→ editor_config.json (프로필 설정)
                │
                ▼
[웹 에디터 UI]
프로필 선택 → 서비스 목록 → 도구 편집
```

---

## 핵심 포인트

1. **언어 자동 감지**: Python/JavaScript 프로젝트 자동 판별
2. **설정 파일 수동 편집 불필요**: 스캔 기반 자동 생성
3. **타입 추적 자동화**:
   - Python: import 경로 따라 BaseModel 추출
   - JavaScript: models 디렉토리에서 Sequelize 모델 추출

---

## 관련 스크립트

| 스크립트 | 역할 |
|----------|------|
| `mcp_service_scanner.py` | 서비스 스캔 + 파라미터 추출 (Python/JS 공통) |
| `extract_types.py` | Python BaseModel 타입 추출 |
| `extract_types_js.py` | JavaScript Sequelize 모델 추출 |
