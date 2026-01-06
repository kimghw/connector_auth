# 사용자 시나리오 - 첨부파일 처리 기능 구현

## 요구사항 요약
사용자는 Outlook 메일 시스템에서 첨부파일을 효율적으로 처리하기 위한 통합 함수 구현을 요청했습니다.

## 주요 요청 사항

### 1. 기존 구조 개선
- batch_and_attachment 메서드에 메타데이터만 조회하는 옵션 추가
- metadata_only 파라미터를 통해 다운로드 없이 정보만 확인 가능하도록 구현

### 2. GraphAttachmentHandler 메서드 통합
- 기존 3개 메서드(fetch_metadata_only, fetch_and_save, fetch_specific_attachments)를 2개의 통합 함수로 재구성
- 메타정보 조회 함수와 다운로드 함수로 분리

### 3. 새로운 함수 구현
#### fetch_attachments_metadata
- 메일 ID 리스트로 메타데이터만 조회
- 메일 본문 포함 (body 필드)
- 첨부파일 정보 포함 (이름, 크기, 타입 등)

#### download_attachments
- 입력 타입에 따라 자동 처리:
  - 메일 ID 리스트: 해당 메일의 모든 첨부파일 다운로드
  - 첨부파일 ID 쌍: 특정 첨부파일만 선택적 다운로드
- 폴더 자동 생성 및 메일 본문 저장 기능 포함

### 4. Facade 패턴 적용
- outlook_service.py에 Facade 함수 구현
- MCP 서비스 데코레이터 적용
- GraphMailClient로 직접 위임하는 구조

### 5. 기타 개선 사항
- SelectParams 객체 직접 처리 지원
- fetch_specific_attachments로 메서드명 변경 (fetch_multiple_attachments → fetch_specific_attachments)
- MCP 용어 지침 준수 (handler_ → handle_ 수정)

## 테스트 요구사항
- 실제 메일 데이터(최근 일주일)로 테스트
- 메타데이터 조회 기능 검증
- 다운로드 기능 검증 (전체/선택적)
- 폴더 구조 및 파일 저장 확인

## 구현 완료 항목
- ✅ 메타데이터 전용 조회 기능
- ✅ 통합 다운로드 함수 (다형성 지원)
- ✅ Facade 패턴 적용
- ✅ 실제 데이터 테스트
- ✅ 용어 지침 준수

---
*작성일: 2025-01-07*
*대화 세션: 첨부파일 처리 기능 구현*
