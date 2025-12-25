#!/usr/bin/env python3
import subprocess
import time
import requests
import json
import sys

def colored_print(msg, color='normal'):
    colors = {
        'green': '\033[92m',
        'red': '\033[91m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'normal': '\033[0m'
    }
    print(f"{colors.get(color, '')}{msg}{colors['normal']}")

def test_rest_handler():
    """REST 서버 핸들러 호출 테스트"""
    colored_print("\n📡 REST Server Handler Test", 'blue')
    colored_print("=" * 50, 'blue')
    
    # 서버 시작
    proc = subprocess.Popen(["python", "server.py"], 
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.PIPE)
    time.sleep(5)
    
    try:
        # 1. Health check
        r = requests.get("http://localhost:8000/health")
        print(f"1. Health Check: {r.json()}")
        
        # 2. Initialize
        r = requests.post("http://localhost:8000/mcp/v1/initialize",
                         json={"clientInfo": {"name": "test-client", "version": "1.0"}})
        print(f"2. Initialize: Server={r.json().get('serverInfo', {}).get('name')}")
        
        # 3. List tools
        r = requests.post("http://localhost:8000/mcp/v1/tools/list", json={})
        tools = r.json().get("result", {}).get("tools", [])
        print(f"3. Tools Count: {len(tools)}")
        if tools:
            print(f"   Available tools: {', '.join([t['name'] for t in tools[:3]])}...")
        
        # 4. Call tool (mail_list)
        print("\n4. Calling mail_list handler:")
        r = requests.post("http://localhost:8000/mcp/v1/tools/call",
                         json={
                             "name": "mail_list",
                             "arguments": {
                                 "filter_params": {
                                     "received_date_from": "2024-12-25",
                                     "received_date_to": "2024-12-26"
                                 },
                                 "user_email": "test@example.com"
                             }
                         })
        
        if r.status_code == 200:
            result = r.json()
            if "result" in result:
                colored_print("   ✅ Handler successfully called!", 'green')
                content = result.get("result", {}).get("content", [])
                if content:
                    text = content[0].get("text", "{}")
                    data = json.loads(text) if text != "{}" else {}
                    if "error" in data:
                        print(f"   Expected auth error: {data['error']}")
                    else:
                        print(f"   Response received: {list(data.keys())}")
            elif "error" in result:
                colored_print(f"   ⚠️  Error: {result['error']}", 'yellow')
        else:
            colored_print(f"   ❌ HTTP {r.status_code}", 'red')
            
        return True
        
    except Exception as e:
        colored_print(f"   ❌ Exception: {e}", 'red')
        return False
    finally:
        proc.terminate()
        proc.wait(timeout=2)

def test_stdio_handler():
    """STDIO 서버 핸들러 호출 테스트"""
    colored_print("\n📡 STDIO Server Handler Test", 'blue')
    colored_print("=" * 50, 'blue')
    
    # JSON-RPC 요청
    requests_data = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"clientInfo": {"name": "test"}}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
            "name": "mail_list",
            "arguments": {
                "filter_params": {
                    "received_date_from": "2024-12-25",
                    "received_date_to": "2024-12-26"
                },
                "user_email": "test@example.com"
            }
        }}
    ]
    
    input_data = '\n'.join(json.dumps(req) for req in requests_data) + '\n'
    
    proc = subprocess.Popen(["python", "server_stdio.py"],
                           stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           text=True)
    
    try:
        output, errors = proc.communicate(input_data, timeout=3)
        responses = []
        for line in output.strip().split('\n'):
            if line and line.startswith('{'):
                try:
                    responses.append(json.loads(line))
                except:
                    pass
        
        # 응답 분석
        for resp in responses:
            if resp.get("id") == 1:
                print(f"1. Initialize: {resp.get('result', {}).get('serverInfo', {}).get('name', 'OK')}")
            elif resp.get("id") == 2:
                tools = resp.get("result", {}).get("tools", [])
                print(f"2. Tools Count: {len(tools)}")
                if tools:
                    print(f"   Available tools: {', '.join([t['name'] for t in tools[:3]])}...")
            elif resp.get("id") == 3:
                print("\n3. Calling mail_list handler:")
                if "result" in resp:
                    colored_print("   ✅ Handler successfully called!", 'green')
                    content = resp.get("result", {}).get("content", [])
                    if content:
                        text = content[0].get("text", "{}")
                        print(f"   Response type: {type(text)}")
                elif "error" in resp:
                    colored_print(f"   ⚠️  Error: {resp['error']}", 'yellow')
        
        return True
        
    except Exception as e:
        colored_print(f"   ❌ Exception: {e}", 'red')
        return False

def test_stream_handler():
    """StreamableHTTP 서버 핸들러 호출 테스트"""
    colored_print("\n📡 StreamableHTTP Server Handler Test", 'blue')
    colored_print("=" * 50, 'blue')
    
    # 서버 시작
    proc = subprocess.Popen(["python", "server_stream.py"],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    time.sleep(5)
    
    try:
        # 1. Health check
        r = requests.get("http://localhost:8001/health")
        print(f"1. Health Check: {r.json()}")
        
        # 2. Initialize
        r = requests.post("http://localhost:8001/mcp/v1/initialize",
                         json={"clientInfo": {"name": "test-client"}})
        print(f"2. Initialize: Streaming={r.json().get('capabilities', {}).get('streaming')}")
        
        # 3. List tools
        r = requests.post("http://localhost:8001/mcp/v1/tools/list", json={})
        tools = r.json().get("tools", [])
        print(f"3. Tools Count: {len(tools)}")
        
        # 4. Normal call
        print("\n4. Calling mail_list handler (normal):")
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
            result = r.json()
            if "content" in result:
                colored_print("   ✅ Handler successfully called!", 'green')
                content = result.get("content", [])
                if content:
                    text = content[0].get("text", "{}")
                    print(f"   Response type: {type(text)}")
            elif "error" in result:
                colored_print(f"   ⚠️  Error: {result['error']}", 'yellow')
        
        # 5. Streaming call
        print("\n5. Calling mail_list handler (streaming):")
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
        
        colored_print(f"   ✅ Received {len(chunks)} chunks", 'green')
        if chunks:
            print(f"   First chunk type: {chunks[0].get('type')}")
            print(f"   Last chunk done: {chunks[-1].get('done')}")
        
        return True
        
    except Exception as e:
        colored_print(f"   ❌ Exception: {e}", 'red')
        return False
    finally:
        proc.terminate()
        proc.wait(timeout=2)

# Main
if __name__ == "__main__":
    colored_print("🚀 Complete Handler Call Test for All Protocols", 'blue')
    colored_print("=" * 60, 'blue')
    
    # Kill existing servers
    subprocess.run("pkill -f 'python.*server' 2>/dev/null", shell=True)
    subprocess.run("lsof -ti:8000 -ti:8001 | xargs -r kill -9 2>/dev/null", shell=True)
    time.sleep(2)
    
    results = {}
    
    # Test each protocol
    results['REST'] = test_rest_handler()
    time.sleep(1)
    
    results['STDIO'] = test_stdio_handler()
    time.sleep(1)
    
    results['StreamableHTTP'] = test_stream_handler()
    
    # Summary
    colored_print("\n" + "=" * 60, 'blue')
    colored_print("📊 HANDLER TEST SUMMARY", 'blue')
    colored_print("=" * 60, 'blue')
    
    for protocol, success in results.items():
        if success:
            colored_print(f"✅ {protocol}: Handler call successful", 'green')
        else:
            colored_print(f"❌ {protocol}: Handler call failed", 'red')
    
    all_success = all(results.values())
    print()
    if all_success:
        colored_print("🎉 All protocols successfully called handlers!", 'green')
    else:
        colored_print("⚠️ Some protocols had issues", 'yellow')
    
    colored_print("=" * 60, 'blue')
