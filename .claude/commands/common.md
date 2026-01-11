# 공통 작업 지침

모든 작업 시 아래 지침을 준수해 주세요.

---

## 1. 사전 검증
- 지침이 올바르지 않거나 로직 상에서 문제가 있다면 사용자에게 관련 내용을 확인해 주세요.

## 2. 분석 단계
사용자 질의 또는 지침에 따라 문제를 우선 분석하고 참조하는 라이브러리나 스크립트를 함께 분석해 주세요.

- **Explore 에이전트 사용**: 코드베이스 탐색 시 활용
- **새로운 기능 추가 시**: 기존 프로젝트와 의존성, 연계성 등을 분석
- **리팩토링/기능 개선 시**: 내부 프로젝트 의존성 관계를 우선 검토 (외부 라이브러리보다 내부 모듈 간 의존성에 집중)
- **디버깅 시**: 문제를 우선 파악하고 현 상황을 분석
- **분석 시**: 기존 코드의 주요 기능은 유지할 수 있도록 작성

### 추상화 검토 기준
모듈 간 의존성 분석 시 아래 조건에 해당하면 **Protocol/인터페이스 추상화**를 검토:

| 조건 | 예시 |
|------|------|
| 다른 구현체로 교체 가능성 | Outlook → Gmail, Teams 등 |
| 모듈 간 경계에서 직접 임포트 | `session` ↔ `mcp_outlook` 상호 참조 |
| 테스트 시 Mock 필요 | 인증, 외부 API 호출 등 |

> **참고**: 같은 모듈 내부나 교체 가능성 없는 유틸리티는 직접 임포트 유지

## 3. 계획 및 TODO 리스트 작성
분석 결과에 따라 계획 및 TODO 리스트를 작성해 주세요.

- 참조하는 라이브러리나 스크립트를 명확히 지정
- 계획 작성 시 테스트 코드도 작성 (테스트 후 삭제)
- 네이밍 규칙 준수: [terminology.md](terminology.md)

## 4. 코드 생성
계획에 따라 코드를 생성해 주세요.

## 5. 테스트 완료
테스트를 완료해 주세요.

## 6. 사용자 시나리오 기록
사용자의 질의 중 중요사항을 다음 파일에 저장해 주세요:
- `/home/kimghw/Connector_auth/.claude/preprompts/usersenario.md`

**저장 기준**:
- "진행해 주세요", "실행해 주세요" 같은 일반적인 요청은 제외
- 구체적인 기능 요청, 버그 수정, 아키텍처 변경 등을 기록
- 최종적으로 요구사항에 맞게 업데이트되었는지 확인

---

## 관련 문서

| 문서 | 설명 |
|------|------|
| [terminology.md](terminology.md) | 네이밍 규칙 및 용어 정의 |
| [web.md](web.md) | 웹에디터 설계 원칙 (대시보드, 병합 포함) |
| [handler.md](handler.md) | 핸들러 파라미터 체계 |
| [mcp_service.md](mcp_service.md) | MCP 서비스 구현 가이드 |
| [test.md](test.md) | 테스트 가이드 |
| [add_protocol.md](add_protocol.md) | 프로토콜 추가 가이드 |

### preprompts 관련 문서

| 문서 | 설명 |
|------|------|
| [web_dataflow.md](../preprompts/web_dataflow.md) | **웹에디터 데이터 흐름 상세** (전체 플로우 종합) |
| [add_config.md](../preprompts/add_config.md) | editor_config.json 자동 업데이트 조건 |
| [usersenario.md](../preprompts/usersenario.md) | 사용자 시나리오 기록 |
| [refact.md](../preprompts/refact.md) | 리팩토링 가이드 |

> **역할 분리**: `web.md`/`handler.md`는 사용 지침, `web_dataflow.md`는 내부 구현 상세

---
*Last Updated: 2026-01-11*
