/**
 * 파생 서버 및 도구 이동 관련 기능
 */

// 파생 서버 생성
async function deriveProfile(baseProfile, newName, port) {
  const response = await fetch('/api/profiles/derive', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      base_profile: baseProfile,
      new_profile_name: newName,
      port: port
    })
  });
  return response.json();
}

// 형제 프로필 조회
async function getSiblingProfiles(profile) {
  const response = await fetch(`/api/profiles/${profile}/siblings`);
  return response.json();
}

// 프로필 가족 관계 조회
async function getProfileFamily(profile) {
  const response = await fetch(`/api/profiles/${profile}/family`);
  return response.json();
}

// 도구 이동
async function moveTools(sourceProfile, targetProfile, toolIndices, mode) {
  const response = await fetch('/api/tools/move', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      source_profile: sourceProfile,
      target_profile: targetProfile,
      tool_indices: toolIndices,
      mode: mode
    })
  });
  return response.json();
}

// 이동 가능 여부 검증
async function validateMove(sourceProfile, targetProfile, toolIndices) {
  const response = await fetch('/api/tools/validate-move', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      source_profile: sourceProfile,
      target_profile: targetProfile,
      tool_indices: toolIndices
    })
  });
  return response.json();
}

// 이동 가능한 도구 목록 조회
async function getMovableTools(sourceProfile, targetProfile) {
  const response = await fetch(`/api/tools/movable?source=${sourceProfile}&target=${targetProfile}`);
  return response.json();
}

// 파생 서버 생성 모달 표시
function showDeriveModal(baseProfile) {
  // 기존 모달 사용 또는 새 모달 생성
  const modal = document.getElementById('derive-modal');
  if (modal) {
    document.getElementById('derive-base').value = baseProfile;
    modal.style.display = 'flex';
  }
}

// 파생 서버 생성 확인
async function confirmDerive() {
  const baseProfile = document.getElementById('derive-base').value;
  const newName = document.getElementById('derive-name').value.trim();
  const port = parseInt(document.getElementById('derive-port').value) || 8092;

  if (!newName) {
    alert('새 프로필 이름을 입력하세요.');
    return;
  }

  try {
    const result = await deriveProfile(baseProfile, newName, port);
    if (result.success) {
      alert(`파생 서버 '${newName}'가 생성되었습니다.`);
      document.getElementById('derive-modal').style.display = 'none';
      // 프로필 목록 새로고침
      if (typeof loadProfiles === 'function') {
        loadProfiles();
      }
    } else {
      alert('오류: ' + result.error);
    }
  } catch (e) {
    alert('오류: ' + e.message);
  }
}

// 모달 닫기
function closeDeriveModal() {
  document.getElementById('derive-modal').style.display = 'none';
}

function closeMoveModal() {
  document.getElementById('move-modal').style.display = 'none';
}

// 도구 이동 대화상자 열기 (체크박스 모드 활성화)
function openMoveToolsDialog() {
  // 도구 선택 모드 활성화
  window.toolSelectMode = !window.toolSelectMode;

  const btn = document.querySelector('[data-debug-id="BTN_MOVE_TOOLS"]');

  if (window.toolSelectMode) {
    // 선택 모드 활성화 - 버튼 스타일 변경
    if (btn) {
      btn.style.background = '#db2777';
      btn.style.color = 'white';
      btn.innerHTML = '<span class="material-icons" style="font-size: 16px;">check_circle</span> 선택 완료';
    }

    // 도구 목록에 체크박스 추가
    addToolCheckboxes();

    // 안내 메시지
    if (typeof showNotification === 'function') {
      showNotification('이동할 도구를 선택한 후 "선택 완료" 버튼을 클릭하세요', 'info');
    }
  } else {
    // 선택 모드 비활성화 - 선택된 도구로 이동 모달 표시
    if (btn) {
      btn.style.background = '#fce7f3';
      btn.style.color = '#db2777';
      btn.innerHTML = '<span class="material-icons" style="font-size: 16px;">drive_file_move</span> 도구 이동';
    }

    // 선택된 도구 인덱스 수집
    const selectedIndices = getSelectedToolIndices();

    if (selectedIndices.length === 0) {
      if (typeof showNotification === 'function') {
        showNotification('이동할 도구를 선택하세요', 'warning');
      } else {
        alert('이동할 도구를 선택하세요');
      }
      // 선택 모드 다시 활성화
      window.toolSelectMode = true;
      if (btn) {
        btn.style.background = '#db2777';
        btn.style.color = 'white';
        btn.innerHTML = '<span class="material-icons" style="font-size: 16px;">check_circle</span> 선택 완료';
      }
      return;
    }

    // 체크박스 제거
    removeToolCheckboxes();

    // 이동 모달 표시
    showMoveToolsModal(window.currentProfile, selectedIndices);
  }
}

// 도구 목록에 체크박스 추가
function addToolCheckboxes() {
  const toolItems = document.querySelectorAll('.tool-item');

  toolItems.forEach((item, index) => {
    // 이미 체크박스가 있으면 스킵
    if (item.querySelector('.tool-select')) return;

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.className = 'tool-select';
    checkbox.dataset.toolIndex = index;
    checkbox.style.cssText = 'position: absolute; left: 8px; top: 50%; transform: translateY(-50%); width: 18px; height: 18px; cursor: pointer; z-index: 10;';
    checkbox.onclick = (e) => e.stopPropagation();

    // 상대 위치 지정을 위해 스타일 추가
    item.style.position = 'relative';
    item.style.paddingLeft = '36px';

    item.insertBefore(checkbox, item.firstChild);
  });
}

// 체크박스 제거
function removeToolCheckboxes() {
  const checkboxes = document.querySelectorAll('.tool-select');
  checkboxes.forEach(cb => {
    const item = cb.parentElement;
    if (item) {
      item.style.paddingLeft = '';
    }
    cb.remove();
  });
}

// 선택된 도구 인덱스 가져오기
function getSelectedToolIndices() {
  const indices = [];
  document.querySelectorAll('.tool-select:checked').forEach(cb => {
    indices.push(parseInt(cb.dataset.toolIndex));
  });
  return indices;
}

// 도구 이동 확인 (수정된 버전)
async function confirmMoveTools() {
  const sourceProfile = window.currentProfile;
  const targetProfile = document.getElementById('move-target').value;
  const mode = document.querySelector('input[name="move-mode"]:checked')?.value || 'move';

  if (!targetProfile) {
    alert('대상 프로필을 선택하세요.');
    return;
  }

  // 선택된 도구 인덱스 - 저장된 값 사용
  const selectedIndices = window.selectedToolIndices || [];

  if (selectedIndices.length === 0) {
    alert('이동할 도구를 선택하세요.');
    return;
  }

  try {
    const result = await moveTools(sourceProfile, targetProfile, selectedIndices, mode);
    if (result.success) {
      alert(`${result.moved_tools.length}개 도구가 ${mode === 'move' ? '이동' : '복사'}되었습니다.`);
      document.getElementById('move-modal').style.display = 'none';
      window.selectedToolIndices = [];
      // 도구 목록 새로고침
      if (typeof loadTools === 'function') {
        loadTools();
      }
    } else {
      alert('오류: ' + result.error);
    }
  } catch (e) {
    alert('오류: ' + e.message);
  }
}

// 도구 이동 모달 표시 (수정된 버전)
async function showMoveToolsModal(sourceProfile, selectedIndices) {
  const modal = document.getElementById('move-modal');
  if (!modal) return;

  // 선택된 인덱스 저장
  window.selectedToolIndices = selectedIndices;

  // 형제 프로필 로드
  try {
    const familyData = await getProfileFamily(sourceProfile);
    const siblings = familyData.derived || [];
    if (familyData.base && familyData.base !== sourceProfile) {
      siblings.unshift(familyData.base);
    }

    // 자신 제외
    const targets = siblings.filter(p => p !== sourceProfile);

    // 타겟 선택 드롭다운 업데이트
    const targetSelect = document.getElementById('move-target');
    if (targets.length > 0) {
      targetSelect.innerHTML = '<option value="">-- 대상 프로필 선택 --</option>' +
        targets.map(t => `<option value="${t}">${t}</option>`).join('');
    } else {
      targetSelect.innerHTML = '<option value="">파생된 프로필이 없습니다</option>';
    }
  } catch (e) {
    console.error('Failed to load profile family:', e);
    // 에러 시 전체 프로필 로드 시도
    try {
      const response = await fetch('/api/profiles');
      const profiles = await response.json();
      const targetSelect = document.getElementById('move-target');
      const targets = profiles.filter(p => p !== sourceProfile);
      targetSelect.innerHTML = '<option value="">-- 대상 프로필 선택 --</option>' +
        targets.map(t => `<option value="${t}">${t}</option>`).join('');
    } catch (e2) {
      console.error('Failed to load profiles:', e2);
    }
  }

  // 선택된 도구 수 표시
  document.getElementById('selected-count').textContent = selectedIndices.length;

  modal.style.display = 'flex';
}

// 전역 함수로 내보내기
window.deriveProfile = deriveProfile;
window.getSiblingProfiles = getSiblingProfiles;
window.getProfileFamily = getProfileFamily;
window.moveTools = moveTools;
window.validateMove = validateMove;
window.showDeriveModal = showDeriveModal;
window.showMoveToolsModal = showMoveToolsModal;
window.confirmDerive = confirmDerive;
window.confirmMoveTools = confirmMoveTools;
window.openMoveToolsDialog = openMoveToolsDialog;
window.addToolCheckboxes = addToolCheckboxes;
window.removeToolCheckboxes = removeToolCheckboxes;
window.getSelectedToolIndices = getSelectedToolIndices;
