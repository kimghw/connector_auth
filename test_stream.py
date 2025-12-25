import requests
import json

# Test server endpoints
base_url = "http://localhost:8002"

print("1. Health Check")
r = requests.get(f"{base_url}/health")
print(json.dumps(r.json(), indent=2))

print("\n2. Initialize")
r = requests.post(f"{base_url}/mcp/v1/initialize",
                  json={"clientInfo": {"name": "test"}})
print(json.dumps(r.json(), indent=2))

print("\n3. Tools List")
r = requests.post(f"{base_url}/mcp/v1/tools/list", json={})
tools = r.json()
print(f"Found {len(tools['tools'])} tools")
print(f"First tool: {tools['tools'][0]['name']}")
print(f"Supports streaming: {tools['tools'][0].get('supportsStreaming', False)}")
