# API에서 Python 스크립트 실행 방법

## 1. subprocess.run() 사용 (권장)

### 기본 사용법
```python
import subprocess
import sys

@app.route('/api/run-script', methods=['POST'])
def run_script():
    try:
        # Python 스크립트 실행
        result = subprocess.run(
            [sys.executable, 'path/to/script.py', 'arg1', 'arg2'],
            capture_output=True,  # stdout, stderr 캡처
            text=True,           # 텍스트 모드 (bytes 대신 string)
            cwd='/working/directory',  # 작업 디렉토리
            timeout=30           # 타임아웃 (초)
        )

        # 결과 확인
        if result.returncode == 0:
            return jsonify({
                "success": True,
                "output": result.stdout,
                "message": "Script executed successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": result.stderr,
                "returncode": result.returncode
            }), 500

    except subprocess.TimeoutExpired:
        return jsonify({"error": "Script execution timed out"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

## 2. 모듈로 Import하여 실행

### 직접 import 방식
```python
@app.route('/api/create-project', methods=['POST'])
def create_project_api():
    try:
        # 모듈 경로를 sys.path에 추가
        sys.path.insert(0, os.path.join(ROOT_DIR, "jinja"))

        # 모듈 import
        from create_mcp_project import MCPProjectCreator

        # 클래스 인스턴스 생성 및 메서드 호출
        creator = MCPProjectCreator(base_dir=ROOT_DIR)
        result = creator.create_project(
            service_name="example",
            description="Example service",
            port=8080
        )

        return jsonify(result)

    except ImportError as e:
        return jsonify({"error": f"Failed to import module: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

## 3. 동적 모듈 로딩 (importlib 사용)

```python
import importlib.util

@app.route('/api/load-module', methods=['POST'])
def load_module_dynamically():
    try:
        # 모듈 동적 로딩
        module_path = os.path.join(ROOT_DIR, "jinja", "generate_editor_config.py")
        spec = importlib.util.spec_from_file_location("generator", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # 모듈의 함수 호출
        result = module.generate_config()

        return jsonify({"success": True, "result": result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

## 4. 실제 사용 예시 (tool_editor_web.py)

### generate_editor_config.py 실행
```python
@app.route('/api/update-editor-config', methods=['POST'])
def update_editor_config():
    """editor_config.json을 자동으로 업데이트"""
    try:
        generate_script = os.path.join(ROOT_DIR, "jinja", "generate_editor_config.py")

        if not os.path.exists(generate_script):
            return jsonify({"error": "generate_editor_config.py not found"}), 404

        # 스크립트 실행
        result = subprocess.run(
            [sys.executable, generate_script],
            capture_output=True,
            text=True,
            cwd=ROOT_DIR,
            timeout=10
        )

        if result.returncode == 0:
            # 프로필 리로드
            global profiles
            profiles = load_profiles()

            return jsonify({
                "success": True,
                "message": "editor_config.json updated successfully",
                "profiles": list(profiles.keys())
            })
        else:
            return jsonify({
                "error": f"Script failed: {result.stderr}"
            }), 500

    except subprocess.TimeoutExpired:
        return jsonify({"error": "Script execution timed out"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

## 5. 비동기 실행 (백그라운드 작업)

```python
import threading

@app.route('/api/run-async', methods=['POST'])
def run_script_async():
    """백그라운드에서 스크립트 실행"""

    def run_in_background():
        try:
            subprocess.run(
                [sys.executable, 'long_running_script.py'],
                capture_output=True,
                text=True
            )
        except Exception as e:
            print(f"Background task failed: {e}")

    # 백그라운드 스레드 시작
    thread = threading.Thread(target=run_in_background)
    thread.daemon = True
    thread.start()

    return jsonify({
        "success": True,
        "message": "Script started in background"
    })
```

## 주의사항

1. **보안**: 사용자 입력을 직접 명령어로 사용하지 마세요
   ```python
   # 위험한 예
   subprocess.run(user_input, shell=True)  # Never do this!

   # 안전한 예
   allowed_scripts = ['script1.py', 'script2.py']
   if script_name in allowed_scripts:
       subprocess.run([sys.executable, script_name])
   ```

2. **타임아웃 설정**: 무한 루프 방지
   ```python
   subprocess.run(..., timeout=30)  # 30초 타임아웃
   ```

3. **에러 처리**: returncode 확인
   ```python
   if result.returncode != 0:
       # 에러 처리
   ```

4. **작업 디렉토리**: cwd 파라미터 사용
   ```python
   subprocess.run(..., cwd=ROOT_DIR)
   ```

5. **Python 인터프리터**: sys.executable 사용
   ```python
   # 현재 Python 인터프리터 사용
   [sys.executable, 'script.py']
   ```

## tool_editor_web.py의 실제 구현

현재 파일에서 이미 사용 중인 예시:

1. **create_mcp_project.py 실행** (줄 1539-1549)
   - 모듈을 import하여 클래스 메서드 직접 호출

2. **generate_editor_config.py 실행 필요**
   - subprocess.run()으로 실행 추가 가능

3. **extract_base_model_schemas.py 실행** (줄 1506)
   - subprocess.run()으로 실행