#!/usr/bin/env python3
import subprocess
import time
import requests
import json
import sys

def test_rest():
    print("=== Testing REST Server ===")
    # Start server
    proc = subprocess.Popen(["python", "server.py"], 
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.PIPE)
    time.sleep(3)
    
    try:
        # Health check
        r = requests.get("http://localhost:8000/health")
        print(f"Health: {r.json()}")
        
        # Tools list
        r = requests.post("http://localhost:8000/mcp/v1/tools/list", json={})
        tools = r.json().get("result", {}).get("tools", [])
        print(f"Tools count: {len(tools)}")
        if tools:
            print(f"First tool: {tools[0]['name']}")
    finally:
        proc.terminate()
        proc.wait(timeout=2)
    print()

def test_stdio():
    print("=== Testing STDIO Server ===")
    # Test with ping
    input_data = '{"jsonrpc":"2.0","id":1,"method":"ping","params":{}}\n'
    proc = subprocess.Popen(["python", "server_stdio.py"],
                           stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           text=True)
    
    output, _ = proc.communicate(input_data, timeout=2)
    lines = output.strip().split('\n')
    for line in lines:
        if '"id": 1' in line:
            response = json.loads(line)
            print(f"Ping response: {response.get('result')}")
            break
    
    # Test tools list
    input_data = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"clientInfo":{"name":"test"}}}\n{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}\n'
    proc = subprocess.Popen(["python", "server_stdio.py"],
                           stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           text=True)
    
    output, _ = proc.communicate(input_data, timeout=2)
    lines = output.strip().split('\n')
    for line in lines:
        if '"id": 2' in line:
            response = json.loads(line)
            tools = response.get("result", {}).get("tools", [])
            print(f"Tools count: {len(tools)}")
            if tools:
                print(f"First tool: {tools[0]['name']}")
            break
    print()

def test_stream():
    print("=== Testing StreamableHTTP Server ===")
    # Start server
    proc = subprocess.Popen(["python", "server_stream.py"],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    time.sleep(3)
    
    try:
        # Health check
        r = requests.get("http://localhost:8001/health")
        print(f"Health: {r.json()}")
        
        # Tools list
        r = requests.post("http://localhost:8001/mcp/v1/tools/list", json={})
        tools = r.json().get("tools", [])
        print(f"Tools count: {len(tools)}")
        if tools:
            print(f"First tool: {tools[0]['name']}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        proc.terminate()
        proc.wait(timeout=2)

if __name__ == "__main__":
    test_rest()
    test_stdio()
    test_stream()
