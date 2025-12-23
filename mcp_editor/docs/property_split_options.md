# Input Schema Property 분리 방식 검토 문서

## 📋 배경

현재 MCP Tool Editor에서 types.py의 클래스를 추가할 때, **전체 객체를 Signature 또는 Internal로만 선택 가능**합니다.

### 사용자 요구사항
같은 클래스(예: FilterParams)에서 **일부 프로퍼티는 Signature로, 일부는 Internal로 분리**하고 싶습니다.

```python
# types.py
class FilterParams(BaseModel):
    field: str          # ← Signature로 노출하고 싶음
    operator: str       # ← Signature로 노출하고 싶음
    value: str          # ← Signature로 노출하고 싶음
    advanced_config: dict  # ← Internal로 숨기고 싶음
    debug_mode: bool    # ← Internal로 숨기고 싶음
```

---

## 🎯 3가지 구현 옵션 비교

### 옵션 1: 객체 내 프로퍼티별 Signature/Internal 혼합

#### 개념
```javascript
// 같은 property 이름에서 프로퍼티를 두 곳에 분산
tool.inputSchema.properties.filter_params = {
  properties: {
    field: {},      // ← Signature
    operator: {},   // ← Signature
    value: {}       // ← Signature
  }
}

internalArgs.filter_params = {
  original_schema: {
    properties: {
      advanced_config: {},  // ← Internal
      debug_mode: {}        // ← Internal
    }
  }
}
```

#### 구현 방법
1. **새 UI 추가**: "Split Class" 버튼 (객체 타입 property에)
2. **Split 모달**: 프로퍼티를 두 그룹으로 분류
3. **데이터 구조 변경**: mixed_mode 플래그 추가
4. **렌더링 로직 수정**: 중첩 프로퍼티마다 destination 선택
5. **저장/로드 수정**: 두 곳에서 병합

#### 난이도 평가
- **복잡도**: ⭐⭐⭐⭐⭐ (매우 높음)
- **수정 파일**: 10+ 곳
- **새 UI**: Split 모달, Merge 모달, 프로퍼티별 destination UI
- **예상 시간**: 4-6시간
- **리스크**: 높음 (기존 로직 대폭 수정)

#### 장점
- ✅ 가장 직관적인 UI
- ✅ 같은 property 이름 유지

#### 단점
- ❌ 구현 복잡도 매우 높음
- ❌ 유지보수 어려움
- ❌ 버그 발생 가능성 높음
- ❌ 테스트 범위 넓음

---

### 옵션 2: 같은 클래스를 다른 이름으로 2번 추가

#### 개념
```javascript
// 1. 같은 클래스를 2번 추가, 다른 이름으로
tool.inputSchema.properties.filter_params_sig = {
  type: "FilterParams",
  properties: {
    field: {},
    operator: {},
    value: {}
  }
}

// 2. Internal로 설정
internalArgs.filter_params_int = {
  type: "FilterParams",
  original_schema: {
    properties: {
      advanced_config: {},
      debug_mode: {}
    }
  }
}

// 3. Generator에서 병합 (선택적)
// → FilterParams(field, operator, value, advanced_config, debug_mode)
```

#### 구현 방법
1. **Add Property 모달 수정**: Property 이름 입력 필드 추가
2. **중복 체크 수정**: 다른 이름이면 허용
3. **병합 힌트 UI**: 같은 baseModel 감지 시 표시
4. **Generator 수정** (선택적): 같은 타입 자동 병합

#### 난이도 평가
- **복잡도**: ⭐⭐⭐ (보통)
- **수정 파일**: 3-4 곳
- **새 UI**: 이름 입력 필드, 병합 힌트 표시
- **예상 시간**: 1-2시간
- **리스크**: 중간

#### 장점
- ✅ 기존 UI/로직 대부분 재사용
- ✅ 유연성 높음 (이름 자유)
- ✅ 각 property 독립적 관리
- ✅ 검증 및 수정 용이

#### 단점
- ❌ Property 이름이 중복 느낌 (filter_params_sig, filter_params_int)
- ❌ Generator 수정 필요 (병합 로직)
- ❌ 사용자가 이름 규칙 이해 필요

---

### 옵션 3: 같은 이름 추가 시 Merge/Replace 선택

#### 개념
```javascript
// 현재 동작:
// 1차: FilterParams → filter_params (field, operator 선택)
filter_params.properties = {field: {}, operator: {}}

// 2차: FilterParams → filter_params (value, config 선택)
// 문제: 자동으로 MERGE됨!
filter_params.properties = {field: {}, operator: {}, value: {}, config: {}}

// 개선: 사용자에게 물어보기
confirm("filter_params already exists. OK=Merge, Cancel=Replace")
```

#### 구현 방법
```javascript
// confirmAddProperty 함수의 Line 3262 부근에 추가

if (tools[index].inputSchema.properties[targetPropName]) {
    const existingProps = Object.keys(
        tools[index].inputSchema.properties[targetPropName].properties || {}
    );

    const action = confirm(
        `Property "${targetPropName}" already has ${existingProps.length} properties:\n` +
        `${existingProps.join(', ')}\n\n` +
        `Click OK to ADD new properties (Merge)\n` +
        `Click Cancel to REPLACE with new properties`
    );

    if (!action) {
        // Replace: 기존 properties 초기화
        tools[index].inputSchema.properties[targetPropName].properties = {};
        tools[index].inputSchema.properties[targetPropName].required = [];
    }
    // Merge는 아무것도 안함 (기존 로직이 자동 merge)
}
```

#### 난이도 평가
- **복잡도**: ⭐ (매우 낮음)
- **수정 파일**: 1곳만
- **코드 추가**: 10-15줄
- **예상 시간**: 10-15분
- **리스크**: 매우 낮음

#### 장점
- ✅ 구현 매우 간단
- ✅ 기존 코드 거의 수정 없음
- ✅ 즉시 테스트 가능
- ✅ 리스크 거의 없음

#### 단점
- ❌ 여전히 같은 property에 모든 프로퍼티가 들어감
- ❌ Signature/Internal 분리는 별도 작업 필요

---

## 🎯 추천 워크플로우 (옵션 3 기반)

### 사용 방법
```
1. FilterParams 전체 추가 (모든 프로퍼티 선택)
   → filter_params 생성 (Signature)
   → {field, operator, value, advanced_config, debug_mode}

2. Add Property → FilterParams 다시 선택
   → advanced_config, debug_mode만 선택

3. "Replace" 선택
   → filter_params = {advanced_config, debug_mode}

4. Destination을 "Internal"로 변경
   → internalArgs.filter_params로 이동

5. Add Property → FilterParams 다시 선택
   → field, operator, value 선택

6. "Replace" 선택 (또는 새로 생성)
   → filter_params = {field, operator, value} (Signature)

최종 결과:
✅ Signature: filter_params {field, operator, value}
✅ Internal: filter_params {advanced_config, debug_mode}
```

---

## 📊 비교 표

| 기준 | 옵션 1 | 옵션 2 | 옵션 3 |
|------|--------|--------|--------|
| 구현 시간 | 4-6시간 | 1-2시간 | 10-15분 |
| 복잡도 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ |
| 수정 파일 수 | 10+ | 3-4 | 1 |
| 직관성 | 매우 높음 | 보통 | 보통 |
| 유지보수성 | 낮음 | 보통 | 높음 |
| 리스크 | 높음 | 중간 | 낮음 |
| 확장성 | 제한적 | 높음 | 보통 |

---

## 🏆 권장사항

### 단계별 접근 (추천)

#### Phase 1: 옵션 3 구현 (즉시)
- **이유**: 10분 만에 기본 기능 제공
- **효과**: Merge/Replace 선택으로 프로퍼티 관리 개선
- **리스크**: 거의 없음

#### Phase 2: 사용자 피드백 수집 (1주)
- 실제 사용 패턴 확인
- 불편한 점 파악
- 추가 기능 필요성 검토

#### Phase 3: 필요시 옵션 2 추가 (선택)
- Phase 1이 부족하다고 판단되면
- Property 이름 직접 입력 기능 추가
- 1-2시간 투자로 완벽한 기능 제공

#### Phase 4: 옵션 1은 보류
- 복잡도 대비 효과 낮음
- 대부분 옵션 2+3으로 해결 가능
- 정말 필요하다는 강력한 요구가 있을 때만 고려

---

## 💡 결론

**옵션 3을 먼저 구현하고, 필요하면 옵션 2를 추가하는 것을 권장합니다.**

- ✅ 최소 투자로 즉시 효과
- ✅ 리스크 최소화
- ✅ 점진적 개선 가능
- ✅ 사용자 피드백 기반 발전

---

## 📝 다음 단계

1. **옵션 선택**: 어느 옵션을 구현할지 결정
2. **구현**: 선택한 옵션 코드 작성
3. **테스트**: 다양한 시나리오 검증
4. **문서화**: 사용 방법 가이드 작성

---

*작성일: 2025-12-23*
*작성자: Claude (MCP Tool Editor 검토)*
