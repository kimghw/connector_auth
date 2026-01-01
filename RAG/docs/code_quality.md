# 코드 품질 관리 가이드

## 개요
Python 코드 품질을 관리하기 위한 도구들과 사용법을 설명합니다.

## 주요 도구

### 1. 코드 포매팅
- **Black**: Python 코드 자동 포매팅
- **isort**: import 문 정렬
- **autoflake**: 사용하지 않는 import 및 변수 제거

### 2. 린팅 (Linting)
- **Ruff**: 빠른 Python 린터 (Flake8 대체)
- **Pylint**: 상세한 코드 분석
- **Flake8**: PEP8 스타일 가이드 검사

### 3. 타입 체킹
- **mypy**: 정적 타입 검사

### 4. 보안 검사
- **bandit**: 보안 취약점 검사
- **safety**: 의존성 취약점 검사
- **pip-audit**: 패키지 보안 감사

### 5. 코드 분석
- **vulture**: 사용하지 않는 코드(dead code) 찾기
- **pipdeptree**: 의존성 트리 확인
- **pipreqs**: 실제 사용 중인 패키지만 추출

## 설치

### 개발 도구 설치
```bash
pip install -r requirements-dev.txt
```

### Pre-commit 설정
```bash
pre-commit install
```

## 사용법

### 1. 자동 코드 정리
```bash
# 모든 코드 포매팅 및 정리
make format

# 또는 개별 실행
autoflake --in-place --remove-all-unused-imports --recursive .
isort . --profile black
black .
```

### 2. 코드 검사
```bash
# 모든 검사 실행
make check-all

# 린팅만
make lint

# 타입 체킹만
make type-check

# 보안 검사만
make security
```

### 3. import 관리
```bash
# 사용하지 않는 import 확인
make check-imports

# 사용하지 않는 import 자동 제거
make fix-imports

# 필요한 패키지만 requirements.txt 생성
pipreqs . --force
```

### 4. Dead Code 찾기
```bash
# 사용하지 않는 코드 찾기
vulture . --min-confidence 80

# 더 자세한 분석
vulture . --verbose
```

### 5. 의존성 관리
```bash
# 의존성 트리 확인
make deps-tree

# 오래된 패키지 확인
make deps-outdated

# 사용하지 않는 패키지 제거
make deps-cleanup
```

## Pre-commit Hooks

커밋 전 자동으로 코드 품질을 검사합니다:

```bash
# 수동으로 모든 파일 검사
pre-commit run --all-files

# 특정 파일만 검사
pre-commit run --files interface_spec.py
```

## VS Code 설정

`.vscode/settings.json` 파일에 추가:

```json
{
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.provider": "isort",
    "[python]": {
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.organizeImports": true
        }
    }
}
```

## 코드 품질 리포트

```bash
# 전체 품질 리포트 생성
make quality-report
```

## 예제: interface_spec.py 정리

```bash
# 1. 사용하지 않는 import 제거
autoflake --in-place --remove-all-unused-imports interface_spec.py

# 2. import 정렬
isort interface_spec.py --profile black

# 3. 코드 포매팅
black interface_spec.py

# 4. 린팅 검사
ruff check interface_spec.py

# 5. 타입 체킹
mypy interface_spec.py

# 6. 사용하지 않는 코드 찾기
vulture interface_spec.py
```

## CI/CD 통합

GitHub Actions 예시:

```yaml
name: Code Quality

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    - run: pip install -r requirements-dev.txt
    - run: make check-all
```

## 권장 사항

1. **커밋 전**: `make format` 실행
2. **PR 전**: `make check-all` 실행
3. **정기적으로**: `make deps-outdated` 확인
4. **프로젝트 시작 시**: `pre-commit install` 실행

## 문제 해결

### import 순환 참조
```bash
# 순환 참조 찾기
python -c "import sys; sys.path.insert(0, '.'); from pycycle import pycycle; pycycle.find_cycles('.')"
```

### 큰 파일 찾기
```bash
find . -type f -name "*.py" -size +100k
```

### 복잡도 높은 함수 찾기
```bash
radon cc . -nc
```