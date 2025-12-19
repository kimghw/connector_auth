#!/bin/bash

# KR365 터널 제거 스크립트
echo "======================================"
echo "KR365 터널 제거 및 재생성"
echo "======================================"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. KR365 프로세스 종료
echo -e "\n${YELLOW}1. KR365 터널 프로세스 종료 (sudo 필요)${NC}"
echo "다음 명령을 실행하세요:"
echo -e "${GREEN}sudo kill 2393${NC}"
echo ""

# 2. 터널 정리
echo -e "${YELLOW}2. 터널 연결 정리${NC}"
cloudflared tunnel cleanup KR365 2>/dev/null || echo "정리할 연결이 없습니다"

# 3. 터널 삭제
echo -e "\n${YELLOW}3. KR365 터널 삭제${NC}"
cloudflared tunnel delete KR365 --force 2>/dev/null || echo "터널을 삭제할 수 없습니다 (활성 연결 있음)"

# 4. 새 터널 생성
echo -e "\n${YELLOW}4. 새 터널 생성${NC}"
read -p "새 터널 이름 (기본: mcp-outlook): " TUNNEL_NAME
TUNNEL_NAME=${TUNNEL_NAME:-mcp-outlook}

cloudflared tunnel create $TUNNEL_NAME

# 5. 터널 ID 가져오기
TUNNEL_ID=$(cloudflared tunnel list | grep $TUNNEL_NAME | awk '{print $1}')
echo -e "${GREEN}✓ 터널 생성 완료 (ID: $TUNNEL_ID)${NC}"

# 6. 설정 파일 생성
echo -e "\n${YELLOW}5. 설정 파일 생성${NC}"
cat > ~/.cloudflared/config.yml << EOF
tunnel: $TUNNEL_ID
credentials-file: $HOME/.cloudflared/$TUNNEL_ID.json

ingress:
  # MCP Outlook 서버
  - hostname: outlook.kimghw.org
    service: http://localhost:3000

  # 기타 서비스 추가 가능
  - hostname: api.kimghw.org
    service: http://localhost:8000

  # 404 페이지
  - service: http_status:404
EOF

echo -e "${GREEN}✓ 설정 파일 생성 완료${NC}"

# 7. DNS 설정
echo -e "\n${YELLOW}6. DNS 레코드 추가${NC}"
cloudflared tunnel route dns $TUNNEL_NAME outlook.kimghw.org || echo "DNS 레코드가 이미 존재합니다"

# 8. 터널 실행
echo -e "\n${YELLOW}7. 터널 시작${NC}"
echo -e "${GREEN}터널을 시작하려면:${NC}"
echo "  cloudflared tunnel run $TUNNEL_NAME"
echo ""
echo -e "${GREEN}백그라운드 실행:${NC}"
echo "  nohup cloudflared tunnel run $TUNNEL_NAME &"
echo ""
echo -e "${GREEN}systemd 서비스로 설치:${NC}"
echo "  sudo cloudflared service install"
echo "  sudo systemctl start cloudflared"