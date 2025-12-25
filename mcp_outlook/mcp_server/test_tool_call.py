#!/usr/bin/env python3
import subprocess
import time
import requests
import json

print("=== Testing Tool Calls on All Protocols ===\n")

# Test REST Server tool call
print("1. REST Server - Calling mail_list tool")
proc = subprocess.Popen(["python", "server.py"], 
                       stdout=subprocess.PIPE, 
                       stderr=subprocess.PIPE)
time.sleep(3)

try:
    r = requests.post("http://localhost:8000/mcp/v1/tools/call", 
                     json={
                         "name": "mail_list",
                         "arguments": {
                             "filter_params": {
                                 "received_date_from": "2024-12-01",
                                 "received_date_to": "2024-12-01"
                             }
                         }
                     })
    result = r.json()
    if "error" in result:
        print(f"   Error: {result['error']}")
    else:
        print(f"   Success: Got response")
except Exception as e:
    print(f"   Exception: {e}")
finally:
    proc.terminate()
    proc.wait(timeout=2)

print("\n2. STDIO Server - Calling mail_list tool")
input_data = '''{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"clientInfo":{"name":"test"}}}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"mail_list","arguments":{"filter_params":{"received_date_from":"2024-12-01","received_date_to":"2024-12-01"}}}}
'''
proc = subprocess.Popen(["python", "server_stdio.py"],
                       stdin=subprocess.PIPE,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE,
                       text=True)

output, _ = proc.communicate(input_data, timeout=3)
lines = output.strip().split('\n')
for line in lines:
    if '"id": 2' in line:
        try:
            response = json.loads(line)
            if "error" in response:
                print(f"   Error: {response['error']}")
            else:
                print(f"   Success: Got response")
        except:
            pass
        break

print("\n3. StreamableHTTP Server - Calling mail_list tool (with streaming)")
proc = subprocess.Popen(["python", "server_stream.py"],
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
time.sleep(3)

try:
    # Normal call
    r = requests.post("http://localhost:8001/mcp/v1/tools/call",
                     json={
                         "name": "mail_list",
                         "arguments": {
                             "filter_params": {
                                 "received_date_from": "2024-12-01",
                                 "received_date_to": "2024-12-01"
                             }
                         },
                         "stream": False
                     })
    result = r.json()
    if "error" in result:
        print(f"   Normal call error: {result['error']}")
    else:
        print(f"   Normal call success")
        
    # Streaming call
    r = requests.post("http://localhost:8001/mcp/v1/tools/call",
                     json={
                         "name": "mail_list",
                         "arguments": {
                             "filter_params": {
                                 "received_date_from": "2024-12-01",
                                 "received_date_to": "2024-12-01"}
                         },
                         "stream": True
                     },
                     stream=True)
    
    chunks = 0
    for line in r.iter_lines():
        if line:
            chunks += 1
    print(f"   Streaming call: Received {chunks} chunks")
    
except Exception as e:
    print(f"   Exception: {e}")
finally:
    proc.terminate()
    proc.wait(timeout=2)

print("\n=== All tests completed ===")
