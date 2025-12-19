#!/bin/bash

# KR365 터널 재시작 스크립트 (root 권한 필요)

echo "======================================"
echo "KR365 터널 재시작 (root 권한 필요)"
echo "======================================"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# root 권한 확인
if [ "$EUID" -ne 0 ]; then
   echo -e "${RED}이 스크립트는 root 권한으로 실행해야 합니다.${NC}"
   echo -e "${YELLOW}사용법: sudo ./restart-kr365-tunnel.sh${NC}"
   exit 1
fi

# 1. 기존 KR365 터널 종료
echo -e "\n${YELLOW}1. 기존 KR365 터널 종료${NC}"
PID=$(ps aux | grep cloudflared | grep "tunnel run --token" | grep -v grep | awk '{print $2}')
if [ ! -z "$PID" ]; then
    kill $PID
    echo -e "${GREEN}✓ KR365 터널 종료됨 (PID: $PID)${NC}"
    sleep 2
else
    echo "실행 중인 KR365 터널이 없습니다."
fi

# 2. 새 설정 파일 생성 (임시)
echo -e "\n${YELLOW}2. 터널 설정 업데이트${NC}"
cat > /tmp/kr365-config.yml << EOF
tunnel: 63e6e3ca-865a-4a41-aebe-9c2e66bf283d
credentials-file: /root/.cloudflared/63e6e3ca-865a-4a41-aebe-9c2e66bf283d.json

ingress:
  # MCP Outlook 서버 (포트 3000으로 라우팅)
  - hostname: outlook.kimghw.org
    service: http://localhost:3000

  # 기타 서브도메인들
  - hostname: api.kimghw.org
    service: http://localhost:8000

  - hostname: www.kimghw.org
    service: http://localhost:80

  - hostname: kimghw.org
    service: http://localhost:80

  # 404 페이지
  - service: http_status:404
EOF

echo -e "${GREEN}✓ 설정 파일 생성 완료${NC}"

# 3. KR365 터널 재시작 (토큰 사용)
echo -e "\n${YELLOW}3. KR365 터널 재시작${NC}"

# 토큰 (기존 프로세스에서 가져온 것)
TOKEN="eyJhIjoiYTMyYzE3ZjQ5NzFhYzU0ZmFlYmVmZmNkOGEzMmQ2ZWQiLCJ0IjoiNjNlNmUzY2EtODY1YS00YTQxLWFlYmUtOWMyZTY2YmYyODNkIiwicyI6IllqVm1ORFZpT1RrdE56VXhPUzAwTkRZM0xXSXpOR0l0T1RBek5XWXlabUZqTWpJeSJ9"

# 백그라운드로 터널 시작
nohup /usr/bin/cloudflared --no-autoupdate tunnel run --token $TOKEN > /var/log/cloudflared.log 2>&1 &

echo -e "${GREEN}✓ KR365 터널 재시작 완료${NC}"

# 4. 상태 확인
sleep 3
echo -e "\n${YELLOW}4. 터널 상태 확인${NC}"
if ps aux | grep cloudflared | grep -v grep > /dev/null; then
    echo -e "${GREEN}✓ 터널이 실행 중입니다${NC}"
    echo ""
    echo "로그 확인: tail -f /var/log/cloudflared.log"
    echo ""
    echo -e "${GREEN}접속 URL: https://outlook.kimghw.org${NC}"
else
    echo -e "${RED}터널 시작 실패${NC}"
    echo "로그를 확인하세요: /var/log/cloudflared.log"
fi