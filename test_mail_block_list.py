"""mail_block_list MCP 서버 테스트"""
import asyncio
import aiohttp
import json


async def test_via_mcp_server():
    """MCP 서버를 통해 mail_block_list 테스트"""

    url = "http://localhost:8000/mcp/v1/tools/call"

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "mail_block_list",
            "arguments": {
                "user_email": "kimghw@krs.co.kr",
                "filter_params": {
                    "received_date_from": "2024-12-17T00:00:00Z",
                    "received_date_to": "2024-12-24T23:59:59Z"
                }
            }
        }
    }

    print("=" * 60)
    print("mail_block_list MCP 서버 테스트")
    print("filter: from_address=block@krs.co.kr (internal arg)")
    print("=" * 60)

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload) as response:
                result = await response.json()

                if "error" in result:
                    print(f"ERROR: {result['error']}")
                    return

                content = result.get("result", {}).get("content", [])
                if content:
                    text = content[0].get("text", "{}")
                    data = json.loads(text)

                    mails = data.get("value", [])
                    print(f"조회된 메일 수: {len(mails)}\n")

                    for i, mail in enumerate(mails[:15], 1):
                        subject = mail.get("subject", "(제목 없음)")[:50]
                        from_addr = mail.get("from", {}).get("emailAddress", {}).get("address", "?")
                        print(f"[{i}] {from_addr}")
                        print(f"    {subject}")
                else:
                    print(f"결과: {result}")

        except aiohttp.ClientConnectorError:
            print("ERROR: MCP 서버에 연결할 수 없습니다.")
            print("서버를 먼저 실행하세요: python mcp_outlook/mcp_server/server.py")


if __name__ == "__main__":
    asyncio.run(test_via_mcp_server())
