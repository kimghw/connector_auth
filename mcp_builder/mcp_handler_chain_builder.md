# MCP Handler Chain Builder 요구사항

## 1. 개요
MCP 서버의 핸들러들을 체인 형식으로 연결하는 웹 기반 빌더 시스템 (`mcp_builder` 폴더에서 작업)

### 1.1 목적
- 기존 서비스 함수들을 불러와 GUI에서 연결하여 새로운 통합 서비스 함수 생성
- 이전 함수의 출력을 다음 함수의 입력으로 전달하는 파이프라인 구축
- `{server_name}_service.py` 파일에 체인 함수 추가 (기존 서비스 파일에 통합)
- 체인된 서비스 함수들을 하나의 통합 서비스 함수로 구성

## 2. UI/UX 요구사항

### 2.1 디자인 참조
- ChatGPT Builder의 UI/UX 디자인 채용
- 직관적인 드래그 앤 드롭 인터페이스
- 시각적 플로우 차트 형태의 핸들러 체인 표현

### 2.2 주요 UI 구성요소
- **핸들러 목록 패널**: 사용 가능한 MCP 핸들러 목록 표시
- **캔버스 영역**: 핸들러 체인을 시각적으로 구성
- **노드 연결 버튼**: 각 노드에 🔗 버튼으로 직접 연결 시작
- **속성 패널**: 선택된 핸들러의 파라미터 설정
- **매핑 패널** (핵심 기능):
  - **노드-투-노드 직접 연결**: 포트가 아닌 노드 단위 연결
  - **인자 직접 매핑 모달**: 연결 후 자동으로 열리는 매핑 인터페이스
  - 스플릿 뷰: 좌측(출력 필드) / 우측(입력 파라미터)
  - 비주얼 매핑: 드래그 앤 드롭 연결선
  - 매핑 테이블: 설정된 매핑 관계 목록
  - 변환 옵션: 각 매핑에 대한 변환 규칙 설정

## 3. 기능 요구사항

### 3.1 핸들러 체인 구성
- 드래그 앤 드롭으로 핸들러를 캔버스에 추가
- **노드 간 직접 연결 방식**:
  - 소스 노드의 🔗 버튼 클릭
  - 타겟 노드 클릭으로 연결 완성
  - 연결 즉시 매핑 모달에서 인자 직접 매칭
- 핸들러 간 연결선으로 실행 순서 표시
- 체인 내 핸들러 순서 변경 가능

### 3.2 파라미터 관리
- **통합 파라미터**: 체인 내 모든 함수의 파라미터를 통합 관리
- **중복 파라미터 처리**:
  - 함수1과 함수2의 동일한 이름의 파라미터 감지
  - **병합 옵션**: 하나의 파라미터로 통합 (동일한 값 사용)
  - **분리 옵션**: 각각 별도 파라미터로 유지 (예: `func1_param`, `func2_param`)
  - 사용자가 GUI에서 선택 가능
- **파라미터 우선순위**:
  1. 함수1의 반환값 (매핑된 경우)
  2. 사용자 입력값
  3. 기본값
- **파라미터 입력 폼**: 각 함수별 필수/선택 파라미터 입력
- **파라미터 유효성 검증**: 타입 및 필수값 검증

### 3.3 데이터 플로우 설정
```
[핸들러 A] → [중간 인터페이스] → [결과 선택] → [핸들러 B]
```

#### 3.3.1 중간 인터페이스 (Production Interactive Data Selection)
- **프로덕션 환경 사용**: 중간 인터페이스는 디버깅이 아닌 실제 프로덕션 환경에서 사용
- **실행 중단점**: 핸들러 실행 후 결과를 GUI에 표시
- **데이터 프리뷰**: 이전 핸들러의 출력을 트리 구조로 시각화
- **인터랙티브 선택**:
  - 체크박스로 전달할 데이터 필드 선택
  - 실시간 데이터 필터링 및 검색
  - 데이터 변환 규칙 적용 (포맷 변경, 값 매핑 등)
- **파라미터 매핑 UI**:
  - 드래그 앤 드롭으로 출력 필드를 입력 파라미터에 연결
  - 시각적 연결선으로 매핑 관계 표시
  - 타입 호환성 검증 (경고/에러 표시)
- **사용자 확인**: 선택한 데이터를 다음 핸들러로 전달하기 전 확인
- **조건부 활성화**: 특정 핸들러 간에만 중간 인터페이스 활성화 옵션

#### 3.3.2 결과 → 파라미터 매핑 (핵심 기능)
- **직접 인자 매핑 방식**:
  - 노드 연결 시 자동으로 매핑 모달 오픈
  - 소스 노드의 모든 출력 필드 표시
  - 타겟 노드의 모든 입력 파라미터 표시
  - 필드와 파라미터를 직접 1:1, 1:N, N:1로 유연하게 매핑
- **매핑 인터페이스**:
  - 왼쪽 패널: 이전 핸들러의 반환값 구조 (트리 뷰)
  - 오른쪽 패널: 다음 핸들러의 입력 파라미터 목록
  - 중앙: 드래그 앤 드롭으로 연결 설정
- **자동 매핑 시각화** (신규):
  - **스마트 매핑 제안**: 타입과 이름 기반 자동 매핑 추천
  - **실시간 미리보기**: 매핑 설정 시 결과 데이터 예시 표시
  - **매핑 관계 시각화**:
    - 연결선 색상: 녹색(매핑됨), 주황색(선택적), 빨강색(필수 누락)
    - 애니메이션: 데이터 흐름을 화살표 애니메이션으로 표현
  - **매핑 상태 인디케이터**:
    ```
    ✅ emails[*].id → message_ids (Array mapping)
    ✅ user_email → user_email (Direct mapping)
    ⚠️ subject → subject (Duplicate - needs resolution)
    ❌ required_param (Missing mapping)
    ```
- **매핑 유형**:
  - **직접 매핑**: `result.email` → `params.to`
  - **배열 매핑**: `result.items[0].id` → `params.item_id`
  - **배열 와일드카드**: `result.emails[*].id` → `params.message_ids[]`
  - **중첩 매핑**: `result.data.user.name` → `params.username`
  - **다중 매핑**: 하나의 반환값을 여러 파라미터에 사용
- **매핑 표현**:
  ```json
  {
    "source": "$.result.mail_id",
    "target": "mail_reference",
    "transform": null,
    "preview": "MSG-12345",
    "confidence": 0.95
  }
  ```
- **시각적 매핑 기능**:
  - 드래그 앤 드롭 매핑 설정
  - 자동 타입 검증 및 경고
  - 실시간 데이터 변환 미리보기
  - 매핑 신뢰도 점수 표시

#### 3.3.3 매핑 규칙
- **전체 전달**: 이전 핸들러의 전체 결과를 전달
- **부분 선택**: 특정 필드만 선택하여 전달
- **변환 규칙**: 간단한 데이터 변환 규칙 적용
- **인터랙티브 모드**: 실행 시점에 GUI로 선택

## 4. 실행 흐름

### 4.1 2개 서비스 함수 체인 예시
```python
# 생성될 통합 서비스 함수 구조
from mcp_service_decorator import mcp_service
from service_registry import get_service_function

@mcp_service
async def chained_service_function(**params):
    """체인된 서비스 함수들을 하나의 통합 함수로 구성"""

    # 1. 서비스 함수 불러오기
    func1 = get_service_function('mail_list')
    func2 = get_service_function('mail_send')

    # 2. 파라미터 분리 및 할당
    # 중복 파라미터 처리 (예: 'subject'가 양쪽에 존재하는 경우)
    func1_params = {
        'folder_id': params.get('folder_id'),
        'max_results': params.get('max_results'),
        'subject': params.get('subject')  # 병합된 경우
        # 또는 'subject': params.get('func1_subject')  # 분리된 경우
    }

    # 3. 첫 번째 함수 실행
    result1 = await func1(**func1_params)

    # 4. 매핑 적용 (함수1 반환값 → 함수2 파라미터)
    func2_params = {
        'to': params.get('to'),
        'body': params.get('body')
    }

    # 매핑 우선순위: 함수1 반환값 > 사용자 입력값
    if 'mail_id' in result1:
        func2_params['reference_id'] = result1['mail_id']  # 함수1 반환값 우선
    else:
        func2_params['reference_id'] = params.get('reference_id')  # 사용자 입력값

    if 'sender' in result1:
        func2_params['to'] = result1['sender']  # 답장 시나리오

    # subject 파라미터 처리 (중복 파라미터)
    if 'subject' in result1:
        func2_params['subject'] = f"Re: {result1['subject']}"  # 함수1 반환값 우선
    else:
        func2_params['subject'] = params.get('subject')  # 사용자 입력값

    # 5. 두 번째 함수 실행
    result2 = await func2(**func2_params)

    return result2

# 서비스 함수로 등록
service_registry.register('chained_mail_workflow', chained_service_function)
```

## 5. 기술 요구사항

### 5.1 프론트엔드
- React 기반 SPA
- Redux를 통한 상태 관리 (복잡한 체인 상태 관리)
- 드래그 앤 드롭 라이브러리 (React DnD)
- 플로우 차트 시각화 (React Flow 권장)

### 5.2 백엔드
- 기존 AST 기반 파라미터 수집 시스템 활용 (mcp_service_scanner.py)
- `{server_name}_service.py` 파일 업데이트 로직 (체인 함수 추가)
- 핸들러 메타데이터 관리 API (기존 MCP_SERVICE_REGISTRY 활용)
- `@mcp_service` 데코레이터 자동 적용

### 5.3 데이터 모델
```json
{
  "service_name": "custom_mail_workflow",
  "service_type": "chained_function",
  "description": "메일 목록 조회 후 자동 발송 워크플로우",
  "functions": [
    {
      "id": "func_1",
      "service_name": "mail_list",
      "params": ["folder_id", "max_results", "subject"],
      "position": { "x": 100, "y": 100 }
    },
    {
      "id": "func_2",
      "service_name": "mail_send",
      "params": ["to", "subject", "body", "reference_id"],
      "position": { "x": 300, "y": 100 }
    }
  ],
  "parameter_config": {
    "duplicates": [
      {
        "param_name": "subject",
        "functions": ["func_1", "func_2"],
        "merge_strategy": "merge",  // "merge" 또는 "separate"
        "merged_name": "subject",  // merge인 경우
        "separate_names": {  // separate인 경우
          "func_1": "search_subject",
          "func_2": "send_subject"
        }
      }
    ]
  },
  "connections": [
    {
      "from": "func_1",
      "to": "func_2",
      "enable_interface": true,  // 중간 인터페이스 활성화
      "interface_config": {
        "show_preview": true,
        "allow_filtering": true,
        "allow_transformation": true
      },
      "mappings": [  // 복수 매핑 지원
        {
          "source_path": "$.mail_id",
          "target_param": "reference_id",
          "priority": 1,  // 우선순위 1 (최우선)
          "required": true
        },
        {
          "source_path": "$.sender",
          "target_param": "to",
          "priority": 1,
          "transform": "email_format"
        },
        {
          "source_path": "$.subject",
          "target_param": "subject",
          "priority": 1,  // 함수1 반환값이 최우선
          "prefix": "Re: "
        }
      ]
    }
  ],
  "output_config": {
    "generate_service_function": true,
    "register_to_service_registry": true,
    "create_mcp_tool": false  // 서비스 함수로만 생성
  }
}
```

## 6. 사용자 워크플로우

### 6.1 빌더 사용 단계
1. **핸들러 선택**: 사용할 핸들러들을 캔버스에 추가
2. **연결 설정**: 핸들러 간 실행 순서 정의
3. **파라미터 설정**: 각 핸들러의 파라미터 입력
4. **매핑 설정**: 핸들러 간 데이터 전달 규칙 정의
5. **프리뷰**: 생성될 코드 미리보기
6. **생성**: `server_{profile}.py` 파일 생성

### 6.2 테스트 모드
- 체인 실행 시뮬레이션
- 각 단계별 데이터 흐름 확인
- 프로덕션 중간 인터페이스 실시간 테스트
- 실제 서비스 함수 호출을 통한 검증

### 6.3 중간 인터페이스 워크플로우
1. **핸들러 A 실행 완료**: 첫 번째 핸들러 결과 생성
2. **자동 매핑 분석 및 제안**:
   - 시스템이 반환값과 파라미터를 자동 분석
   - 높은 신뢰도 매핑 자동 연결 (90% 이상)
   - 중간 신뢰도 매핑 제안 표시 (50-90%)
3. **매핑 인터페이스 표시**:
   - 왼쪽: 반환값 트리
     ```
     📁 result1 (fetch_search)
     ├── ✅ emails[] (Array<Mail>)
     │   ├── id: "MSG-001"
     │   ├── subject: "Project Update"
     │   └── sender: "john@example.com"
     ├── ✅ total: 25
     └── ✅ user: "user@example.com"
     ```
   - 오른쪽: 다음 핸들러 파라미터
     ```
     📥 batch_and_process
     ├── ✅ message_ids[] (Required) ← emails[*].id [Auto-mapped]
     ├── ✅ user_email (Required) ← user [Auto-mapped]
     ├── ⚠️ processing_mode (Optional) [Not mapped]
     └── ❌ save_directory (Required) [Missing]
     ```
4. **시각적 매핑 상태**:
   - 🟢 **자동 매핑**: `emails[*].id → message_ids` (신뢰도: 98%)
   - 🟡 **제안 매핑**: `user → user_email` (신뢰도: 85%)
   - 🔴 **수동 필요**: `save_directory` (필수 파라미터)
   - 🔵 **선택적**: `processing_mode` (기본값 있음)
5. **매핑 작업**:
   - 자동 매핑 확인/수정
   - 수동 매핑 추가 (드래그 앤 드롭)
   - 고정값 입력 (필요시)
   - 변환 규칙 적용 (예: prefix "Re: ")
6. **실시간 프리뷰**:
   ```javascript
   // 매핑 결과 예시
   {
     message_ids: ["MSG-001", "MSG-002", "MSG-003"],
     user_email: "user@example.com",
     save_directory: "/tmp/attachments",  // 사용자 입력
     processing_mode: "FULL"  // 기본값
   }
   ```
7. **매핑 검증**:
   - ✅ 모든 필수 파라미터 매핑됨
   - ✅ 타입 호환성 확인
   - ⚠️ 경고: 중복 파라미터 'subject' 처리 필요
8. **확인 및 실행**:
   - 매핑 구성 저장
   - 다음 핸들러 실행
   - 실행 로그 실시간 표시

## 7. 확장성 고려사항

### 7.1 다중 핸들러 지원
- 2개 이상의 핸들러 체인 구성
- 분기 및 조건부 실행 지원
- 병렬 실행 옵션

### 7.2 템플릿 저장
- 자주 사용하는 체인을 템플릿으로 저장
- 템플릿 공유 기능
- 버전 관리

## 8. 보안 고려사항
- 파라미터 유효성 검증
- SQL 인젝션 방지
- XSS 방지
- 권한 관리 (체인 생성/수정/삭제)

## 9. 성능 요구사항
- 실시간 UI 업데이트
- 대용량 데이터 처리 시 페이지네이션
- 비동기 처리로 UI 블로킹 방지

## 10. 서비스 함수 통합

### 10.1 기존 시스템과의 통합
- 생성된 체인 함수를 기존 `{server_name}_service.py` 파일에 추가
- `@mcp_service` 데코레이터 자동 적용 (기존 decorator 구조 활용)
- AST 기반 파라미터 자동 수집 및 메타데이터 관리
- 기존 MCP_SERVICE_REGISTRY와 완전 통합

### 10.2 생성 옵션
- **서비스 함수 추가 모드**: 기존 서비스 파일에 체인 함수 추가
- **독립 모듈 모드**: 별도 체인 모듈 생성 (선택사항)
- **자동 등록**: 생성된 함수를 서비스 레지스트리에 자동 등록

### 10.3 코드 생성 전략
```python
# 기존 {server_name}_service.py 파일에 추가될 체인 함수
@mcp_service(
    tool_name="{{chain_name}}",
    server_name="{{server_name}}",
    service_name="{{chain_name}}",
    description="{{description}}",
    category="chained_service",
    tags=["chain", "workflow"],
    priority={{priority}}
)
async def {{chain_name}}(
    self,
    # 통합된 파라미터들 (중복 처리 완료)
    {{combined_parameters}}
) -> Dict[str, Any]:
    """{{description}}"""

    # 1. 첫 번째 서비스 함수 호출
    func1_result = await self.{{first_function}}(
        {{first_function_params}}
    )

    # 2. 매핑 적용
    {{mapping_logic}}

    # 3. 두 번째 서비스 함수 호출
    func2_result = await self.{{second_function}}(
        {{second_function_params}}
    )

    return func2_result
```

## 11. GUI 매핑 시각화 구현 (신규)

### 11.1 노드 간 직접 연결 방식 (핵심 구현)

#### 11.1.1 연결 패러다임
- **노드-투-노드 연결**: 포트 대신 노드 자체를 연결
  - 각 노드에 연결 버튼(🔗) 배치
  - 소스 노드 버튼 클릭 → 타겟 노드 클릭으로 연결
  - 연결 즉시 매핑 모달 자동 열림
- **직접 인자 매칭**:
  - 1:1 포트 매칭이 아닌 전체 노드 간 연결
  - 연결 후 출력 필드와 입력 파라미터를 직접 매핑
  - 다중 필드를 다중 파라미터에 유연하게 매핑 가능

#### 11.1.2 연결 프로세스
```javascript
// 1. 연결 시작
function startConnection(sourceNodeId) {
  // 소스 노드에 시각적 피드백 (pulsing animation)
  sourceNode.addClass('connecting');

  // 연결 가능한 노드들 강조
  targetNodes.forEach(node => {
    node.addClass('connectable');
  });

  // 임시 연결선 표시
  showTempConnectionLine(sourceNode);
}

// 2. 연결 완료
function completeConnection(targetNodeId) {
  // 연결선 생성
  createConnection(sourceNodeId, targetNodeId);

  // 매핑 모달 자동 열기
  openMappingModal({
    source: sourceNode.service,
    target: targetNode.service,
    onSave: (mappings) => saveFieldMappings(connectionId, mappings)
  });
}

// 3. 인자 직접 매핑
function mapArguments(sourceOutputs, targetInputs) {
  return {
    // 출력 필드 → 입력 파라미터 직접 매핑
    mappings: [
      {
        from: "emails[*].id",      // 소스 노드 출력
        to: "message_ids",          // 타겟 노드 입력
        transform: "array_extract"  // 변환 규칙
      }
    ]
  };
}
```

#### 11.1.3 매핑 인터페이스
- **모달 구조**:
  ```
  ┌─────────────────────────────────────────┐
  │  Source Output        Target Input      │
  │  ┌─────────────┐     ┌─────────────┐   │
  │  │ emails      │ →→→ │ message_ids │   │
  │  │ └─[*]       │     │             │   │
  │  │   └─id      │     │             │   │
  │  │ user_email  │ →→→ │ user_email  │   │
  │  │ folder_id   │     │ folder_id   │   │
  │  └─────────────┘     └─────────────┘   │
  │                                         │
  │  [Auto-map] [Clear] [Cancel] [Save]    │
  └─────────────────────────────────────────┘
  ```

### 11.2 매핑 뷰어 컴포넌트
```javascript
// MappingViewer Component
const MappingViewer = ({ sourceData, targetParams, mappings }) => {
  return (
    <div className="mapping-container">
      {/* 왼쪽: 소스 데이터 트리 */}
      <SourceDataTree data={sourceData} />

      {/* 중앙: 매핑 연결선 */}
      <MappingConnections mappings={mappings} />

      {/* 오른쪽: 타겟 파라미터 */}
      <TargetParamsList params={targetParams} mappings={mappings} />

      {/* 하단: 매핑 상태 요약 */}
      <MappingSummary mappings={mappings} params={targetParams} />
    </div>
  );
};
```

### 11.2 자동 매핑 엔진
```python
class AutoMappingEngine:
    """자동 매핑 추천 엔진"""

    def suggest_mappings(self, source_schema, target_params):
        suggestions = []

        for param in target_params:
            # 1. 이름 기반 매칭
            name_match = self.find_name_match(param.name, source_schema)

            # 2. 타입 기반 매칭
            type_match = self.find_type_match(param.type, source_schema)

            # 3. 신뢰도 계산
            confidence = self.calculate_confidence(name_match, type_match)

            if confidence > 0.5:
                suggestions.append({
                    'source': name_match or type_match,
                    'target': param.name,
                    'confidence': confidence,
                    'auto_apply': confidence > 0.9
                })

        return suggestions
```

### 11.3 매핑 상태 표시
```typescript
interface MappingStatus {
  source: string;           // "emails[*].id"
  target: string;           // "message_ids"
  status: 'mapped' | 'suggested' | 'missing' | 'invalid';
  confidence: number;       // 0.0 ~ 1.0
  transform?: string;       // "to_list", "uppercase", etc
  preview?: any;           // 실제 변환 결과 미리보기
  error?: string;          // 에러 메시지
}

// 시각적 표현
const MappingIndicator = ({ mapping }: { mapping: MappingStatus }) => {
  const getStatusColor = () => {
    switch(mapping.status) {
      case 'mapped': return '#28a745';      // 녹색
      case 'suggested': return '#ffc107';   // 노란색
      case 'missing': return '#dc3545';     // 빨간색
      case 'invalid': return '#6c757d';     // 회색
    }
  };

  return (
    <div className="mapping-indicator">
      <div className="status-dot" style={{ backgroundColor: getStatusColor() }} />
      <span className="source">{mapping.source}</span>
      <Arrow animated={true} />
      <span className="target">{mapping.target}</span>
      {mapping.confidence && (
        <span className="confidence">{(mapping.confidence * 100).toFixed(0)}%</span>
      )}
      {mapping.preview && (
        <Tooltip content={JSON.stringify(mapping.preview)}>
          <Icon name="preview" />
        </Tooltip>
      )}
    </div>
  );
};
```

### 11.4 실시간 매핑 검증
```python
@app.post("/api/validate-mapping")
async def validate_mapping(
    source_data: Dict[str, Any],
    mapping: MappingRule,
    target_param: ParameterInfo
) -> Dict[str, Any]:
    """실시간 매핑 검증 및 미리보기"""

    try:
        # 1. 소스 경로 추출
        value = extract_value(source_data, mapping.source_path)

        # 2. 변환 적용
        if mapping.transform:
            value = apply_transform(value, mapping.transform)

        # 3. 타입 검증
        is_valid = validate_type(value, target_param.type)

        # 4. 미리보기 생성
        preview = truncate_preview(value, max_length=100)

        return {
            "valid": is_valid,
            "preview": preview,
            "actual_type": type(value).__name__,
            "expected_type": target_param.type,
            "warnings": generate_warnings(value, target_param)
        }

    except Exception as e:
        return {
            "valid": False,
            "error": str(e)
        }
```

### 11.5 매핑 사용자 경험 개선
- **드래그 시작**: 소스 필드 하이라이트
- **드래그 중**: 호환 가능한 타겟 필드 강조
- **드롭 시**: 즉시 연결선 생성 및 검증
- **매핑 완료**: 체크마크 애니메이션
- **에러 발생**: 흔들림 애니메이션 및 툴팁

## 12. 통합 포인트

### 12.1 기존 코드베이스 활용
- **mcp_service_decorator.py**: 파라미터 캡처 및 메타데이터 관리
- **mcp_service_scanner.py**: AST 기반 서비스 함수 분석
- **MCP_SERVICE_REGISTRY**: 전역 서비스 레지스트리
- **tool_editor_web.py**: 웹 에디터 기반 확장

### 11.2 파일 구조 통합
- 각 서버의 `mcp_{server_name}` 폴더 구조 유지
- `{server_name}_service.py` 파일에 체인 함수 직접 추가
- 기존 임포트 및 의존성 구조 보존

## 12. 프로젝트 구조
### 12.1 디렉토리 구성
```
mcp_builder/
├── chain_builder/          # 체인 빌더 핵심 모듈
│   ├── __init__.py
│   ├── chain_manager.py    # 체인 관리 로직
│   ├── mapper.py           # 파라미터 매핑 엔진
│   └── generator.py        # 코드 생성기
├── static/                 # 정적 파일
│   ├── css/
│   │   └── chain-builder.css
│   └── js/
│       └── chain-builder.js
├── templates/              # HTML 템플릿
│   └── chain_builder.html
├── web_static/            # 웹 리소스
│   └── images/
├── chain_builder_web.py   # 웹 서버 메인
├── mock_services.py       # 테스트용 목 서비스
└── test_chain_creation.py # 테스트 코드
```

### 12.2 작업 위치
- 모든 체인 빌더 관련 코드는 `mcp_builder` 폴더 내에 위치
- `mcp_editor`의 기존 컴포넌트 재사용 (AST 파서, 서비스 스캐너 등)
- `mcp_service_registry`와 직접 연동
- 생성된 체인 함수는 각 `mcp_{server_name}` 폴더의 서비스 파일에 추가

## 13. 핵심 차별점

### 13.1 기존 구조 활용
- Jinja 템플릿 대신 AST를 통한 직접 코드 수정
- 이미 구현된 `@mcp_service` 데코레이터 시스템 활용
- 각 서버별 `{server_name}_service.py` 파일 구조 유지

### 13.2 프로덕션 중심 설계
- 중간 인터페이스는 프로덕션 환경에서 실제 사용
- 실시간 데이터 매핑 및 변환
- 사용자 인터랙션을 통한 동적 체인 실행

## 14. 실제 구현 예시

### 14.1 자동 매핑 시각화 예시
```
┌─────────────────────────────────────────────────────────────────┐
│                    CHAIN: mail_workflow_complete                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                    │
│  [fetch_search 결과]            매핑           [batch_process 입력]│
│  ┌──────────────────┐    ═══════════════>    ┌─────────────────┐│
│  │ ✅ emails[]      │    Auto (98%)          │ message_ids[]   ││
│  │   ├─ id: "MSG1" │ ──────────────────────> │   ["MSG1",      ││
│  │   ├─ id: "MSG2" │                         │    "MSG2",      ││
│  │   └─ id: "MSG3" │                         │    "MSG3"]      ││
│  │                  │                         │                 ││
│  │ ✅ user          │    Auto (95%)          │ user_email      ││
│  │   "john@ex.com" │ ──────────────────────> │   "john@ex.com" ││
│  │                  │                         │                 ││
│  │ ⚠️ subject       │    Duplicate           │ ⚠️ subject      ││
│  │   "Project"     │ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─> │   [처리 필요]   ││
│  │                  │                         │                 ││
│  │ 📊 total: 25    │    Not mapped           │ ❌ save_dir     ││
│  └──────────────────┘                         │   [필수 입력]   ││
│                                               └─────────────────┘│
│                                                                    │
│  매핑 상태:                                                        │
│  ✅ 자동 매핑: 2개 (emails→message_ids, user→user_email)         │
│  ⚠️ 중복 파라미터: 1개 (subject - 병합/분리 선택 필요)            │
│  ❌ 누락 필수: 1개 (save_directory - 사용자 입력 필요)           │
│                                                                    │
│  [매핑 검증] [코드 미리보기] [체인 저장]                          │
└─────────────────────────────────────────────────────────────────┘
```

### 14.2 생성된 코드와 매핑 관계
```python
# GUI에서 설정한 매핑이 코드로 변환
async def mail_workflow_complete(self, ...):
    # Step 1: fetch_search 실행
    result_1 = await self.fetch_search(...)

    # Step 2: 자동 매핑 적용 (GUI에서 확인한 내용)
    # ✅ emails[*].id → message_ids (배열 매핑)
    message_ids = [item.get("id") for item in result_1.get("emails", [])]

    # ✅ user → user_email (직접 매핑)
    user_email = result_1.get("user")

    # ⚠️ subject 중복 처리 (사용자 선택에 따라)
    if merge_strategy == "merge":
        subject = params.get("subject")  # 동일 값 사용
    else:
        search_subject = params.get("search_subject")
        batch_subject = params.get("batch_subject")

    # Step 3: batch_process 실행
    result_2 = await self.batch_process(
        message_ids=message_ids,
        user_email=user_email,
        save_directory=params.get("save_directory")  # 사용자 입력
    )
```

### 14.3 실시간 매핑 검증 API 응답
```json
{
  "mappings": [
    {
      "source": "$.emails[*].id",
      "target": "message_ids",
      "status": "valid",
      "confidence": 0.98,
      "preview": ["MSG-001", "MSG-002", "MSG-003"],
      "transform": "array_extract",
      "auto_applied": true
    },
    {
      "source": "$.user",
      "target": "user_email",
      "status": "valid",
      "confidence": 0.95,
      "preview": "john@example.com",
      "auto_applied": true
    },
    {
      "source": null,
      "target": "save_directory",
      "status": "missing",
      "required": true,
      "message": "필수 파라미터입니다. 사용자 입력이 필요합니다."
    }
  ],
  "validation": {
    "is_valid": false,
    "missing_required": ["save_directory"],
    "duplicate_params": ["subject"],
    "auto_mapped_count": 2,
    "manual_required_count": 1
  }
}