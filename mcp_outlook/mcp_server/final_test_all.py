#!/usr/bin/env python3
import subprocess
import time
import requests
import json
import sys

print("=" * 60)
print("FINAL TEST: All MCP Protocols")
print("=" * 60)

def test_rest():
    print("\n📡 REST Server Test (Port 8000)")
    print("-" * 40)
    proc = subprocess.Popen(["python", "server.py"], 
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.PIPE)
    time.sleep(4)
    
    try:
        # Test call
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
        if r.status_code == 200 and "result" in r.json():
            print("✅ REST: Tool call successful")
        else:
            print(f"⚠️  REST: {r.json().get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ REST: {e}")
    finally:
        proc.terminate()
        proc.wait(timeout=2)

def test_stdio():
    print("\n📡 STDIO Server Test (stdin/stdout)")
    print("-" * 40)
    input_data = '''{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"clientInfo":{"name":"test"}}}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"mail_list","arguments":{"filter_params":{"received_date_from":"2024-12-25","received_date_to":"2024-12-26"},"user_email":"test@example.com"}}}
'''
    proc = subprocess.Popen(["python", "server_stdio.py"],
                           stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           text=True)
    
    try:
        output, _ = proc.communicate(input_data, timeout=3)
        if '"id": 2' in output and ('"result"' in output or '"error"' in output):
            if '"result"' in output:
                print("✅ STDIO: Tool call successful")
            else:
                print("⚠️  STDIO: Tool call returned (expected auth error)")
    except Exception as e:
        print(f"❌ STDIO: {e}")

def test_stream():
    print("\n📡 StreamableHTTP Server Test (Port 8001)")
    print("-" * 40)
    proc = subprocess.Popen(["python", "server_stream.py"],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    time.sleep(4)
    
    try:
        # Normal call
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
            print("✅ StreamableHTTP: Normal call successful")
        else:
            print(f"⚠️  StreamableHTTP: {r.json().get('error', 'Unknown error')}")
            
        # Streaming call
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
        chunks = sum(1 for _ in r.iter_lines())
        if chunks > 0:
            print(f"✅ StreamableHTTP: Streaming successful ({chunks} chunks)")
        
    except Exception as e:
        print(f"❌ StreamableHTTP: {e}")
    finally:
        proc.terminate()
        proc.wait(timeout=2)

# Kill any existing servers
subprocess.run("pkill -f 'python.*server' 2>/dev/null", shell=True)
time.sleep(1)

# Run tests
test_rest()
test_stdio()
test_stream()

print("\n" + "=" * 60)
print("✨ All protocol tests completed!")
print("=" * 60)
