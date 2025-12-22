# CLI vs API 엔드포인트 실행 차이

## 1. CLI 실행 (Command Line)

### 특징
- **독립 프로세스**: 새로운 Python 프로세스 생성
- **직접 실행**: 스크립트를 직접 실행
- **터미널 출력**: print()가 터미널에 바로 표시
- **인자 전달**: sys.argv 또는 argparse로 처리

### 예시: create_mcp_project.py
```python
# CLI 실행
$ python jinja/create_mcp_project.py weather --port 8080 --author "John"

# 내부 동작
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("service_name")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()  # sys.argv 파싱

    creator = MCPProjectCreator()
    result = creator.create_project(
        service_name=args.service_name,
        port=args.port
    )

    # 결과를 터미널에 직접 출력
    print(f"✅ Created: {result}")
    sys.exit(0)  # 프로세스 종료
```

## 2. API 엔드포인트 실행

### 특징
- **서버 프로세스 내**: Flask/FastAPI 서버 프로세스에서 실행
- **HTTP 통신**: 요청/응답 패턴
- **JSON 반환**: 결과를 JSON으로 직렬화
- **비동기 가능**: 백그라운드 작업 가능

### 예시: tool_editor_web.py
```python
# API 엔드포인트
@app.route('/api/create-mcp-project', methods=['POST'])
def create_new_mcp_project():
    # HTTP 요청 본문에서 데이터 추출
    data = request.json
    service_name = data.get("service_name")
    port = data.get("port", 8080)

    # 모듈을 import (이미 메모리에 로드)
    from create_mcp_project import MCPProjectCreator

    creator = MCPProjectCreator()
    result = creator.create_project(
        service_name=service_name,
        port=port
    )

    # JSON으로 응답
    return jsonify({
        "success": True,
        "result": result
    })  # 서버는 계속 실행됨
```

## 3. 주요 차이점

| 구분 | CLI | API 엔드포인트 |
|------|-----|--------------|
| **실행 방식** | `python script.py args` | HTTP POST 요청 |
| **프로세스** | 새 프로세스 생성 | 기존 서버 프로세스 사용 |
| **입력** | 명령줄 인자 (argv) | HTTP 요청 본문 (JSON) |
| **출력** | stdout/stderr (터미널) | HTTP 응답 (JSON) |
| **에러 처리** | sys.exit(1), 예외 발생 | HTTP 상태 코드 (400, 500) |
| **사용자** | 개발자 (터미널) | 웹 UI 사용자 |
| **상태 유지** | 상태 없음 (실행 후 종료) | 서버 메모리에 상태 유지 가능 |
| **동시성** | 각각 독립 실행 | 서버가 여러 요청 동시 처리 |

## 4. 실제 사용 예시

### CLI에서 subprocess로 다른 스크립트 실행
```python
# create_mcp_project.py 내부
def _run_generate_editor_config(self):
    # 새로운 Python 프로세스로 generate_editor_config.py 실행
    result = subprocess.run(
        [sys.executable, "jinja/generate_editor_config.py"],
        capture_output=True,
        text=True
    )
```

### API에서 두 가지 방식

#### 방법 1: 모듈 import (같은 프로세스)
```python
@app.route('/api/create-project', methods=['POST'])
def create_project():
    # 같은 프로세스 내에서 실행 (빠름, 메모리 공유)
    from create_mcp_project import MCPProjectCreator
    creator = MCPProjectCreator()
    result = creator.create_project(...)
    return jsonify(result)
```

#### 방법 2: subprocess (별도 프로세스)
```python
@app.route('/api/run-script', methods=['POST'])
def run_script():
    # 별도 프로세스로 실행 (격리됨, 느림)
    result = subprocess.run(
        [sys.executable, "script.py"],
        capture_output=True
    )
    return jsonify({"output": result.stdout})
```

## 5. 장단점 비교

### CLI 실행
**장점:**
- 간단하고 직관적
- 스크립팅 및 자동화 용이
- 독립적 실행 (격리)

**단점:**
- 웹 UI 통합 어려움
- 매번 프로세스 생성 오버헤드

### API 엔드포인트
**장점:**
- 웹 UI와 통합 용이
- RESTful 인터페이스
- 원격 접근 가능
- 상태 유지 가능

**단점:**
- 서버 설정 필요
- HTTP 오버헤드
- 보안 고려사항 많음

## 6. 선택 기준

- **CLI 사용**: 개발자 도구, 배치 작업, 스크립트 자동화
- **API 사용**: 웹 애플리케이션, 원격 접근, UI 통합

## 현재 프로젝트 구조

우리 프로젝트에서는 **두 방식 모두 지원**:

1. **CLI 지원**:
   ```bash
   python jinja/create_mcp_project.py service_name
   ```

2. **API 지원**:
   웹 UI의 "New Project" 버튼 → `/api/create-mcp-project` 엔드포인트

3. **내부 동작**:
   - 두 방식 모두 같은 `MCPProjectCreator` 클래스 사용
   - 코드 재사용으로 일관성 유지