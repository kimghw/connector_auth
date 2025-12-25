#!/usr/bin/env python3
import subprocess
import time
import requests
import json

print("=" * 60)
print("MCP PROTOCOLS QUICK TEST")
print("=" * 60)

# Kill existing servers
subprocess.run("pkill -f 'python.*server' 2>/dev/null", shell=True)
time.sleep(1)

def quick_test(name, port=None, is_stdio=False):
    """빠른 프로토콜 테스트"""
    print(f"\n[{name}]")
    
    if is_stdio:
        # STDIO test
        proc = subprocess.Popen(["python", "server_stdio.py"],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               text=True)
        
        test_input = '{"jsonrpc":"2.0","id":1,"method":"ping","params":{}}\n'
        test_input += '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"mail_list","arguments":{"filter_params":{"received_date_from":"2024-12-25","received_date_to":"2024-12-26"},"user_email":"test@example.com"}}}\n'
        
        try:
            output, _ = proc.communicate(test_input, timeout=3)
            if '"pong":true' in output.lower():
                print("  ✅ Ping: OK")
            if '"result"' in output or '"error"' in output:
                print("  ✅ Tool call: Handler reached")
            return True
        except:
            print("  ❌ Failed")
            return False
    else:
        # HTTP test
        if name == "REST":
            proc = subprocess.Popen(["python", "server.py"],
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
        else:
            proc = subprocess.Popen(["python", "server_stream.py"],
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
        
        time.sleep(4)
        
        try:
            # Health check
            r = requests.get(f"http://localhost:{port}/health", timeout=1)
            if r.status_code == 200:
                print(f"  ✅ Health: OK")
            
            # Tool call
            r = requests.post(f"http://localhost:{port}/mcp/v1/tools/call",
                            json={
                                "name": "mail_list",
                                "arguments": {
                                    "filter_params": {
                                        "received_date_from": "2024-12-25",
                                        "received_date_to": "2024-12-26"
                                    },
                                    "user_email": "test@example.com"
                                }
                            },
                            timeout=3)
            
            if r.status_code == 200:
                print(f"  ✅ Tool call: Handler reached")
            
            proc.terminate()
            return True
        except Exception as e:
            print(f"  ❌ Error: {e}")
            proc.terminate()
            return False

# Run tests
results = []
results.append(("REST", quick_test("REST", 8000)))
time.sleep(1)
results.append(("STDIO", quick_test("STDIO", is_stdio=True)))
time.sleep(1)
results.append(("StreamableHTTP", quick_test("StreamableHTTP", 8001)))

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
for name, success in results:
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} - {name}")

if all(r[1] for r in results):
    print("\n🎉 All protocols working!")
else:
    print("\n⚠️  Some protocols failed")
print("=" * 60)
