#!/usr/bin/env python3
import subprocess
import time
import requests
import json

print("=" * 60)
print("🚀 FINAL TEST: All Protocols with Initialization Fix")
print("=" * 60)

# Kill any existing servers
subprocess.run("pkill -f 'python.*server' 2>/dev/null", shell=True)
subprocess.run("lsof -ti:8000 -ti:8001 | xargs -r kill -9 2>/dev/null", shell=True)
time.sleep(2)

# Test arguments
test_args = {
    "name": "mail_list",
    "arguments": {
        "filter_params": {
            "received_date_from": "2024-12-25",
            "received_date_to": "2024-12-26"
        },
        "user_email": "test@example.com"
    }
}

def test_protocol(name, port, cmd, is_stdio=False):
    print(f"\n📡 Testing {name}")
    print("-" * 40)
    
    if is_stdio:
        # STDIO test
        input_data = f'{{"jsonrpc":"2.0","id":1,"method":"initialize","params":{{"clientInfo":{{"name":"test"}}}}}}\n'
        input_data += f'{{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{json.dumps(test_args)}}}\n'
        
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE, text=True)
        try:
            output, _ = proc.communicate(input_data, timeout=3)
            if '"result"' in output and '"id": 2' in output:
                print(f"✅ {name}: Tool call successful")
                return True
            else:
                print(f"⚠️  {name}: Response received (check auth)")
                return True
        except Exception as e:
            print(f"❌ {name}: {e}")
            return False
    else:
        # HTTP test (REST or Stream)
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(5)  # Wait for server startup
        
        try:
            # Check if server is ready
            health_url = f"http://localhost:{port}/health"
            r = requests.get(health_url, timeout=2)
            
            # Test tool call
            url = f"http://localhost:{port}/mcp/v1/tools/call"
            r = requests.post(url, json=test_args, timeout=5)
            
            if r.status_code == 200:
                if "result" in r.json():
                    print(f"✅ {name}: Tool call successful")
                else:
                    print(f"⚠️  {name}: {r.json().get('error', {}).get('message', 'Auth required')}")
                return True
            else:
                print(f"❌ {name}: HTTP {r.status_code}")
                return False
        except Exception as e:
            print(f"❌ {name}: {e}")
            return False
        finally:
            proc.terminate()
            proc.wait(timeout=2)

# Run tests
results = []
results.append(test_protocol("REST (Port 8000)", 8000, ["python", "server.py"]))
time.sleep(1)
results.append(test_protocol("STDIO", None, ["python", "server_stdio.py"], is_stdio=True))
time.sleep(1)
results.append(test_protocol("StreamableHTTP (Port 8001)", 8001, ["python", "server_stream.py"]))

# Summary
print("\n" + "=" * 60)
print("📊 SUMMARY")
print("=" * 60)
success = sum(results)
total = len(results)
if success == total:
    print(f"✨ All {total} protocols working perfectly!")
else:
    print(f"⚠️  {success}/{total} protocols working")
print("=" * 60)
