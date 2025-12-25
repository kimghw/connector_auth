import requests
import json

# REST 서버에 직접 호출
url = "http://localhost:8000/mcp/v1/tools/call"
payload = {
    "name": "mail_list",
    "arguments": {
        "filter_params": {
            "received_date_from": "2024-12-25",
            "received_date_to": "2024-12-26"
        }
    }
}

print("Sending payload:", json.dumps(payload, indent=2))
response = requests.post(url, json=payload)
print("\nResponse status:", response.status_code)
print("Response body:", response.text)
