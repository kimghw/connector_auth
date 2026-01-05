#!/usr/bin/env python3
"""
MCP Server Manager
Manages MCP server processes with PID file tracking and process control
"""

import os
import sys
import json
import time
import psutil
import subprocess
from typing import Optional, Dict, List

# Get the root directory where all MCP modules are located
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PID_DIR = os.path.join(ROOT_DIR, ".mcp_pids")
LOG_DIR = os.path.join(ROOT_DIR, ".mcp_logs")

# Ensure directories exist
os.makedirs(PID_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)


class MCPServerManager:
    """Manages MCP server lifecycle with PID file tracking"""

    def __init__(self, profile: str = "default"):
        self.profile = profile
        self.pid_file = os.path.join(PID_DIR, f"{profile}_server.pid")
        self.log_file = os.path.join(LOG_DIR, f"{profile}_server.log")
        self.server_path = self._get_server_path()

    def _get_server_path(self) -> Optional[str]:
        """Get the server path based on profile - checks for multiple server types"""
        server_files = ["server_rest.py", "server_stdio.py", "server_stream.py", "server.py"]

        if "outlook" in self.profile.lower():
            base_path = os.path.join(ROOT_DIR, "mcp_outlook", "mcp_server")
        elif "file" in self.profile.lower() or "handler" in self.profile.lower():
            base_path = os.path.join(ROOT_DIR, "mcp_file_handler", "mcp_server")
        else:
            # Default or try to find any server
            for module in ["mcp_outlook", "mcp_file_handler"]:
                base_path = os.path.join(ROOT_DIR, module, "mcp_server")
                # Check if any server file exists in this path
                for server_file in server_files:
                    if os.path.exists(os.path.join(base_path, server_file)):
                        break
                else:
                    continue
                break
            else:
                return None

        # Return the first existing server file in the base path
        for server_file in server_files:
            path = os.path.join(base_path, server_file)
            if os.path.exists(path):
                return path

        return None

    def _read_pid(self) -> Optional[int]:
        """Read PID from file"""
        if os.path.exists(self.pid_file):
            try:
                with open(self.pid_file, "r") as f:
                    return int(f.read().strip())
            except (ValueError, FileNotFoundError):
                return None
        return None

    def _write_pid(self, pid: int):
        """Write PID to file"""
        with open(self.pid_file, "w") as f:
            f.write(str(pid))

    def _remove_pid(self):
        """Remove PID file"""
        if os.path.exists(self.pid_file):
            os.remove(self.pid_file)

    def _is_process_running(self, pid: int) -> bool:
        """Check if a process with given PID is running"""
        try:
            process = psutil.Process(pid)
            # Check if it's actually our Python server
            if process.is_running():
                cmdline = " ".join(process.cmdline())
                # Check for any server file (server.py, server_rest.py, server_stdio.py, server_stream.py)
                return "python" in process.name().lower() and ("server.py" in cmdline or "server_" in cmdline)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        return False

    def _find_server_processes(self) -> List[Dict]:
        """Find all MCP server processes (managed or unmanaged)"""
        processes = []

        # First check managed process
        pid = self._read_pid()
        if pid and self._is_process_running(pid):
            try:
                proc = psutil.Process(pid)
                processes.append(
                    {"pid": pid, "cmd": " ".join(proc.cmdline()), "managed": True, "profile": self.profile}
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                self._remove_pid()

        # Also look for unmanaged processes
        if self.server_path:
            # Get just the filename for more flexible matching
            server_filename = os.path.basename(self.server_path)

            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    if proc.info["cmdline"] and proc.info["pid"] != pid:
                        cmdline = " ".join(proc.info["cmdline"])

                        # Check if this is a python process running our server file
                        if "python" in proc.info["name"].lower() and server_filename in cmdline:
                            # Additional check: make sure it's the right module (outlook or file_handler)
                            if "outlook" in self.profile.lower():
                                # For outlook profile, accept if running server_rest.py without explicit path check
                                # since it could be started from various directories
                                if server_filename in cmdline:
                                    processes.append(
                                        {"pid": proc.info["pid"], "cmd": cmdline, "managed": False, "profile": "unknown"}
                                    )
                            elif "file" in self.profile.lower() or "handler" in self.profile.lower():
                                # Similar for file_handler
                                if server_filename in cmdline:
                                    processes.append(
                                        {"pid": proc.info["pid"], "cmd": cmdline, "managed": False, "profile": "unknown"}
                                    )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        return processes

    def status(self) -> Dict:
        """Get server status"""
        processes = self._find_server_processes()
        # Get the primary managed process PID
        managed_processes = [p for p in processes if p.get("managed")]
        primary_pid = managed_processes[0]["pid"] if managed_processes else None

        return {
            "running": len(processes) > 0,
            "pid": primary_pid,  # Add primary PID for UI display
            "processes": processes,
            "profile": self.profile,
            "server_path": self.server_path,
        }

    def start(self, detached: bool = True) -> Dict:
        """Start the server"""
        # Check if already running
        status = self.status()
        if status["running"]:
            managed = [p for p in status["processes"] if p["managed"]]
            if managed:
                return {
                    "success": False,
                    "error": f"Server already running with PID {managed[0]['pid']}",
                    "pid": managed[0]["pid"],
                }

        if not self.server_path:
            return {"success": False, "error": f"Server path not found for profile: {self.profile}"}

        # Start the server
        try:
            if detached:
                # Start in background with proper detachment
                with open(self.log_file, "w") as log:
                    process = subprocess.Popen(
                        [sys.executable, self.server_path],
                        cwd=os.path.dirname(self.server_path),
                        stdout=log,
                        stderr=subprocess.STDOUT,
                        start_new_session=True,
                        close_fds=True,
                    )

                # Give it a moment to start
                time.sleep(1)

                if process.poll() is None:
                    # Process is running
                    self._write_pid(process.pid)
                    return {
                        "success": True,
                        "pid": process.pid,
                        "message": f"Server started with PID {process.pid}",
                        "log_file": self.log_file,
                    }
                else:
                    # Process failed to start
                    with open(self.log_file, "r") as log:
                        error_output = log.read()
                    return {"success": False, "error": f"Server failed to start: {error_output}"}
            else:
                # Run in foreground (for debugging)
                subprocess.run([sys.executable, self.server_path], cwd=os.path.dirname(self.server_path))
                return {"success": True, "message": "Server ran in foreground mode"}

        except Exception as e:
            return {"success": False, "error": f"Failed to start server: {str(e)}"}

    def stop(self, force: bool = False) -> Dict:
        """Stop the server"""
        processes = self._find_server_processes()
        if not processes:
            return {"success": False, "error": "No server process found"}

        killed_count = 0
        errors = []

        for proc_info in processes:
            pid = proc_info["pid"]
            try:
                process = psutil.Process(pid)
                if force:
                    process.kill()  # SIGKILL
                else:
                    process.terminate()  # SIGTERM

                # Wait for process to terminate
                try:
                    process.wait(timeout=5)
                except psutil.TimeoutExpired:
                    if not force:
                        # If gentle termination failed, force kill
                        process.kill()
                        process.wait(timeout=2)

                killed_count += 1

                # Remove PID file if it was managed
                if proc_info["managed"]:
                    self._remove_pid()

            except psutil.NoSuchProcess:
                # Process already gone
                if proc_info["managed"]:
                    self._remove_pid()
                killed_count += 1
            except Exception as e:
                errors.append(f"Failed to stop PID {pid}: {str(e)}")

        if killed_count > 0:
            return {
                "success": True,
                "message": f"Stopped {killed_count} server process(es)",
                "errors": errors if errors else None,
            }
        else:
            return {"success": False, "error": "Failed to stop any processes", "errors": errors}

    def restart(self) -> Dict:
        """Restart the server"""
        # Stop the server
        stop_result = self.stop()

        # Wait a moment
        time.sleep(1)

        # Start the server
        start_result = self.start()

        return {"success": start_result.get("success", False), "stop_result": stop_result, "start_result": start_result}

    def logs(self, lines: int = 50) -> str:
        """Get recent log output"""
        if not os.path.exists(self.log_file):
            return "No log file found"

        try:
            with open(self.log_file, "r") as f:
                all_lines = f.readlines()
                return "".join(all_lines[-lines:])
        except Exception as e:
            return f"Error reading log file: {str(e)}"


def main():
    """CLI interface for server management"""
    import argparse

    parser = argparse.ArgumentParser(description="MCP Server Manager")
    parser.add_argument("action", choices=["start", "stop", "restart", "status", "logs"], help="Action to perform")
    parser.add_argument("--profile", default="default", help="Profile name (default, outlook, file_handler, etc.)")
    parser.add_argument("--force", action="store_true", help="Force kill the server (for stop action)")
    parser.add_argument("--foreground", action="store_true", help="Run server in foreground (for start action)")
    parser.add_argument("--lines", type=int, default=50, help="Number of log lines to show (for logs action)")

    args = parser.parse_args()

    manager = MCPServerManager(args.profile)

    if args.action == "status":
        result = manager.status()
        print(json.dumps(result, indent=2))

    elif args.action == "start":
        result = manager.start(detached=not args.foreground)
        print(json.dumps(result, indent=2))

    elif args.action == "stop":
        result = manager.stop(force=args.force)
        print(json.dumps(result, indent=2))

    elif args.action == "restart":
        result = manager.restart()
        print(json.dumps(result, indent=2))

    elif args.action == "logs":
        print(manager.logs(lines=args.lines))
        result = {"success": True}  # Initialize result for logs action

    sys.exit(0 if result.get("success", True) else 1)


if __name__ == "__main__":
    main()
