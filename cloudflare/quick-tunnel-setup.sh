#!/bin/bash

# 빠른 Cloudflare Tunnel 설정 (outlook.kimghw.com만)

set -e

echo "========================================"
echo "Cloudflare Tunnel 빠른 설정"
echo "도메인: outlook.kimghw.com"
echo "========================================"

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. Cloudflare 로그인
echo -e "\n${YELLOW}1. Cloudflare 로그인${NC}"
cloudflared tunnel login

# 2. 터널 생성
TUNNEL_NAME="outlook-tunnel"
echo -e "\n${YELLOW}2. 터널 생성: $TUNNEL_NAME${NC}"
cloudflared tunnel create $TUNNEL_NAME

# 3. 터널 ID 가져오기
TUNNEL_ID=$(cloudflared tunnel list | grep $TUNNEL_NAME | awk '{print $1}')
echo -e "${GREEN}✓ 터널 ID: $TUNNEL_ID${NC}"

# 4. 설정 파일 생성
echo -e "\n${YELLOW}3. 설정 파일 생성${NC}"
mkdir -p $HOME/.cloudflared
cat > $HOME/.cloudflared/config.yml << EOF
tunnel: $TUNNEL_ID
credentials-file: $HOME/.cloudflared/$TUNNEL_ID.json

ingress:
  - hostname: outlook.kimghw.com
    service: http://localhost:3000
  - service: http_status:404
EOF

echo -e "${GREEN}✓ 설정 파일 생성 완료${NC}"

# 5. DNS 레코드 추가
echo -e "\n${YELLOW}4. DNS 레코드 추가${NC}"
cloudflared tunnel route dns $TUNNEL_NAME outlook.kimghw.com

echo -e "\n${GREEN}========================================"
echo "설정 완료!"
echo "========================================${NC}"
echo ""
echo "터널 실행:"
echo "  cloudflared tunnel run $TUNNEL_NAME"
echo ""
echo "백그라운드 실행:"
echo "  nohup cloudflared tunnel run $TUNNEL_NAME &"
echo ""
echo "URL: https://outlook.kimghw.com"