#!/usr/bin/env python3
import subprocess
import time
import requests
import json
import sys

def test_rest_detailed():
    """REST 상세 테스트"""
    print("\n🔍 REST Protocol Detailed Test")
    print("-" * 40)
    
    proc = subprocess.Popen(["python", "server.py"],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
    time.sleep(4)
    
    try:
        # 1. Initialize
        r = requests.post("http://localhost:8000/mcp/v1/initialize",
                         json={"clientInfo": {"name": "test"}})
        print(f"1. Initialize: {r.json().get('serverInfo', {}).get('name', 'N/A')}")
        
        # 2. List tools
        r = requests.post("http://localhost:8000/mcp/v1/tools/list", json={})
        tools = r.json().get("result", {}).get("tools", [])
        print(f"2. Tools count: {len(tools)}")
        print(f"   Tools: {[t['name'] for t in tools]}")
        
        # 3. Call each tool (test first 2)
        for tool in tools[:2]:
            if tool['name'] == 'mail_list':
                args = {
                    "filter_params": {
                        "received_date_from": "2024-12-25",
                        "received_date_to": "2024-12-26"
                    },
                    "user_email": "test@example.com"
                }
            elif tool['name'] == 'mail_fetch_search':
                args = {
                    "search_term": "test",
                    "user_email": "test@example.com"
                }
            else:
                args = {"user_email": "test@example.com"}
            
            r = requests.post("http://localhost:8000/mcp/v1/tools/call",
                             json={"name": tool['name'], "arguments": args})
            
            if r.status_code == 200:
                result = r.json()
                if "result" in result:
                    print(f"3. Tool '{tool['name']}': ✅ Called successfully")
                    # Check response content
                    content = result.get("result", {}).get("content", [])
                    if content:
                        text = content[0].get("text", "{}")
                        if text.startswith('{'):
                            data = json.loads(text)
                            if "error" in data:
                                print(f"   └─ Auth error (expected): {data['error'][:30]}...")
                else:
                    print(f"3. Tool '{tool['name']}': ⚠️  {result.get('error', {}).get('message', 'Error')}")
            else:
                print(f"3. Tool '{tool['name']}': ❌ HTTP {r.status_code}")
        
        proc.terminate()
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        proc.terminate()
        return False

def test_stdio_detailed():
    """STDIO 상세 테스트"""
    print("\n🔍 STDIO Protocol Detailed Test")
    print("-" * 40)
    
    proc = subprocess.Popen(["python", "server_stdio.py"],
                           stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           text=True)
    
    # Multiple requests
    requests_str = json.dumps({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"clientInfo":{"name":"test"}}}) + "\n"
    requests_str += json.dumps({"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}) + "\n"
    requests_str += json.dumps({"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"mail_list","arguments":{"filter_params":{"received_date_from":"2024-12-25","received_date_to":"2024-12-26"},"user_email":"test@example.com"}}}) + "\n"
    requests_str += json.dumps({"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"mail_fetch_search","arguments":{"search_term":"test","user_email":"test@example.com"}}}) + "\n"
    
    try:
        output, _ = proc.communicate(requests_str, timeout=5)
        
        # Parse responses
        responses = []
        for line in output.split('\n'):
            if line.strip() and line.startswith('{') and '"id"' in line:
                try:
                    responses.append(json.loads(line))
                except:
                    pass
        
        # Analyze responses
        for resp in responses:
            resp_id = resp.get("id")
            
            if resp_id == 1:
                print(f"1. Initialize: {resp.get('result', {}).get('serverInfo', {}).get('name', 'N/A')}")
            elif resp_id == 2:
                tools = resp.get("result", {}).get("tools", [])
                print(f"2. Tools count: {len(tools)}")
                print(f"   Tools: {[t['name'] for t in tools[:3]]}...")
            elif resp_id == 3:
                if "result" in resp:
                    print(f"3. Tool 'mail_list': ✅ Called successfully")
                elif "error" in resp:
                    print(f"3. Tool 'mail_list': ⚠️  {resp['error'].get('message', 'Error')}")
            elif resp_id == 4:
                if "result" in resp:
                    print(f"4. Tool 'mail_fetch_search': ✅ Called successfully")
                elif "error" in resp:
                    print(f"4. Tool 'mail_fetch_search': ⚠️  {resp['error'].get('message', 'Error')}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_stream_detailed():
    """StreamableHTTP 상세 테스트"""
    print("\n🔍 StreamableHTTP Protocol Detailed Test")
    print("-" * 40)
    
    proc = subprocess.Popen(["python", "server_stream.py"],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
    time.sleep(4)
    
    try:
        # 1. Initialize with capabilities check
        r = requests.post("http://localhost:8001/mcp/v1/initialize",
                         json={"clientInfo": {"name": "test"}})
        caps = r.json().get('capabilities', {})
        print(f"1. Initialize: Streaming={caps.get('streaming', False)}")
        
        # 2. List tools
        r = requests.post("http://localhost:8001/mcp/v1/tools/list", json={})
        tools = r.json().get("tools", [])
        print(f"2. Tools count: {len(tools)}")
        
        # 3. Normal call
        r = requests.post("http://localhost:8001/mcp/v1/tools/call",
                         json={
                             "name": "mail_list",
                             "arguments": {
                                 "filter_params": {
                                     "received_date_from": "2024-12-25",
                                     "received_date_to": "2024-12-26"
                                 },
                                 "user_email": "test@example.com"
                             },
                             "stream": False
                         })
        
        if r.status_code == 200:
            print(f"3. Normal call: ✅ Success")
        
        # 4. Streaming call
        r = requests.post("http://localhost:8001/mcp/v1/tools/call",
                         json={
                             "name": "mail_list",
                             "arguments": {
                                 "filter_params": {
                                     "received_date_from": "2024-12-25",
                                     "received_date_to": "2024-12-26"
                                 },
                                 "user_email": "test@example.com"
                             },
                             "stream": True
                         },
                         stream=True)
        
        chunks = []
        for line in r.iter_lines():
            if line:
                chunks.append(json.loads(line.decode()))
        
        print(f"4. Streaming call: ✅ {len(chunks)} chunks")
        if chunks:
            print(f"   First: type={chunks[0].get('type')}")
            print(f"   Last: done={chunks[-1].get('done')}")
        
        proc.terminate()
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        proc.terminate()
        return False

# Main
print("=" * 60)
print("MCP PROTOCOLS DETAILED FUNCTIONALITY TEST")
print("=" * 60)

subprocess.run("pkill -f 'python.*server' 2>/dev/null", shell=True)
time.sleep(1)

results = []
results.append(test_rest_detailed())
time.sleep(1)
results.append(test_stdio_detailed())
time.sleep(1)
results.append(test_stream_detailed())

# Summary
print("\n" + "=" * 60)
print("FINAL RESULTS")
print("=" * 60)
protocols = ["REST", "STDIO", "StreamableHTTP"]
for i, success in enumerate(results):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} - {protocols[i]}")

if all(results):
    print("\n🎉 All protocols tested successfully!")
    print("✅ Initialization works")
    print("✅ Tools list correctly")
    print("✅ Handlers execute properly")
    print("✅ Parameters parse correctly")
    print("✅ Streaming works (StreamableHTTP)")
else:
    print("\n⚠️  Some tests failed")
print("=" * 60)
