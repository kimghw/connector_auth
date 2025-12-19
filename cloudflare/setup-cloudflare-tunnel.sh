#!/bin/bash

# Cloudflare Tunnel 설정 스크립트
# 사용법: ./setup-cloudflare-tunnel.sh

set -e

echo "========================================"
echo "Cloudflare Tunnel 설정 시작"
echo "========================================"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. cloudflared 설치 확인
echo -e "\n${YELLOW}1. cloudflared 설치 확인${NC}"
if command -v cloudflared &> /dev/null; then
    echo -e "${GREEN}✓ cloudflared가 이미 설치되어 있습니다.${NC}"
    cloudflared --version
else
    echo -e "${YELLOW}cloudflared를 설치합니다...${NC}"
    wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
    sudo dpkg -i cloudflared-linux-amd64.deb
    rm cloudflared-linux-amd64.deb
    echo -e "${GREEN}✓ cloudflared 설치 완료${NC}"
fi

# 2. Cloudflare 로그인
echo -e "\n${YELLOW}2. Cloudflare 계정 로그인${NC}"
echo "브라우저가 열립니다. Cloudflare에 로그인하고 도메인을 선택하세요."
read -p "계속하려면 Enter를 누르세요..."
cloudflared tunnel login

# 3. 터널 이름 입력
echo -e "\n${YELLOW}3. 터널 생성${NC}"
read -p "터널 이름을 입력하세요 (예: my-app-tunnel): " TUNNEL_NAME
if [ -z "$TUNNEL_NAME" ]; then
    TUNNEL_NAME="connector-auth-tunnel"
fi

# 4. 터널 생성
echo -e "${YELLOW}터널 '$TUNNEL_NAME' 생성 중...${NC}"
cloudflared tunnel create $TUNNEL_NAME

# 5. 터널 ID 가져오기
TUNNEL_ID=$(cloudflared tunnel list | grep $TUNNEL_NAME | awk '{print $1}')
echo -e "${GREEN}✓ 터널 생성 완료 (ID: $TUNNEL_ID)${NC}"

# 6. 도메인 입력
echo -e "\n${YELLOW}4. 도메인 설정${NC}"
read -p "기본 도메인을 입력하세요 (예: example.com): " DOMAIN
if [ -z "$DOMAIN" ]; then
    echo -e "${RED}도메인은 필수 입력 항목입니다!${NC}"
    exit 1
fi

# 7. config.yml 업데이트
echo -e "\n${YELLOW}5. 설정 파일 생성${NC}"
CONFIG_FILE="$HOME/.cloudflared/config.yml"
mkdir -p $HOME/.cloudflared

cat > $CONFIG_FILE << EOF
tunnel: $TUNNEL_ID
credentials-file: $HOME/.cloudflared/$TUNNEL_ID.json

ingress:
  # MCP Outlook 서버
  - hostname: outlook.$DOMAIN
    service: http://localhost:3000

  # MCP File Handler 서버
  - hostname: files.$DOMAIN
    service: http://localhost:3001

  # MCP Editor 서버
  - hostname: editor.$DOMAIN
    service: http://localhost:8080

  # OAuth Callback 서버
  - hostname: auth.$DOMAIN
    service: http://localhost:5000

  # API 서버
  - hostname: api.$DOMAIN
    service: http://localhost:8000

  # 메인 웹사이트
  - hostname: $DOMAIN
    service: http://localhost:80

  # www 서브도메인
  - hostname: www.$DOMAIN
    service: http://localhost:80

  # 404 페이지
  - service: http_status:404
EOF

echo -e "${GREEN}✓ 설정 파일 생성 완료: $CONFIG_FILE${NC}"

# 8. DNS 레코드 추가
echo -e "\n${YELLOW}6. DNS 레코드 추가${NC}"
echo "다음 서브도메인들을 추가합니다:"
SUBDOMAINS=("outlook" "files" "editor" "auth" "api" "www" "@")

for subdomain in "${SUBDOMAINS[@]}"; do
    if [ "$subdomain" = "@" ]; then
        echo -e "  - $DOMAIN"
        cloudflared tunnel route dns $TUNNEL_NAME $DOMAIN || true
    else
        echo -e "  - $subdomain.$DOMAIN"
        cloudflared tunnel route dns $TUNNEL_NAME $subdomain.$DOMAIN || true
    fi
done

echo -e "${GREEN}✓ DNS 레코드 추가 완료${NC}"

# 9. 서비스 설치 옵션
echo -e "\n${YELLOW}7. 서비스 설치 (선택사항)${NC}"
read -p "systemd 서비스로 설치하시겠습니까? (y/N): " INSTALL_SERVICE
if [[ $INSTALL_SERVICE =~ ^[Yy]$ ]]; then
    sudo cloudflared service install
    sudo systemctl start cloudflared
    sudo systemctl enable cloudflared
    echo -e "${GREEN}✓ cloudflared 서비스 설치 및 시작 완료${NC}"
fi

# 10. 완료 메시지
echo -e "\n${GREEN}========================================"
echo "설정 완료!"
echo "========================================${NC}"
echo -e "\n사용 가능한 URL:"
echo "  - https://outlook.$DOMAIN (MCP Outlook)"
echo "  - https://files.$DOMAIN (File Handler)"
echo "  - https://editor.$DOMAIN (Editor)"
echo "  - https://auth.$DOMAIN (OAuth Callback)"
echo "  - https://api.$DOMAIN (API Server)"
echo "  - https://$DOMAIN (Main Website)"
echo ""
echo -e "${YELLOW}터널 시작 명령어:${NC}"
echo "  cloudflared tunnel run $TUNNEL_NAME"
echo ""
echo -e "${YELLOW}백그라운드 실행:${NC}"
echo "  nohup cloudflared tunnel run $TUNNEL_NAME &"
echo ""
echo -e "${YELLOW}상태 확인:${NC}"
echo "  cloudflared tunnel info $TUNNEL_NAME"
echo "  systemctl status cloudflared (서비스로 설치한 경우)"