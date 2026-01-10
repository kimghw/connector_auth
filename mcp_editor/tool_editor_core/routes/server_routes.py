"""
Server Control Routes

MCP 서버 제어 API 엔드포인트:
- GET /api/server/status
- POST /api/server/start
- POST /api/server/stop
- POST /api/server/restart
- GET /api/server/logs
"""

from flask import request, jsonify

from . import server_bp


@server_bp.route("/api/server/status", methods=["GET"])
def get_server_status():
    """Check if MCP server is running"""
    try:
        from mcp_server_controller import MCPServerManager

        profile = request.args.get("profile", "default")
        manager = MCPServerManager(profile)
        result = manager.status()

        return jsonify(result)
    except Exception as e:
        return jsonify({"running": False, "error": str(e)})


@server_bp.route("/api/server/start", methods=["POST"])
def start_server():
    """Start the MCP server"""
    try:
        from mcp_server_controller import MCPServerManager

        profile = request.args.get("profile", "default")
        manager = MCPServerManager(profile)
        result = manager.start()

        if result.get("success"):
            return jsonify(result)
        else:
            return jsonify(result), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@server_bp.route("/api/server/stop", methods=["POST"])
def stop_server():
    """Stop the MCP server"""
    try:
        from mcp_server_controller import MCPServerManager

        profile = request.args.get("profile", "default")
        force = request.json.get("force", False) if request.json else False
        manager = MCPServerManager(profile)
        result = manager.stop(force=force)

        if result.get("success"):
            return jsonify(result)
        else:
            return jsonify(result), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@server_bp.route("/api/server/restart", methods=["POST"])
def restart_server():
    """Restart the MCP server"""
    try:
        from mcp_server_controller import MCPServerManager

        profile = request.args.get("profile", "default")
        manager = MCPServerManager(profile)
        result = manager.restart()

        if result.get("success"):
            return jsonify(result)
        else:
            return jsonify(result), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@server_bp.route("/api/server/logs", methods=["GET"])
def get_server_logs():
    """Get MCP server logs"""
    try:
        from mcp_server_controller import MCPServerManager

        profile = request.args.get("profile", "default")
        lines = int(request.args.get("lines", 50))
        manager = MCPServerManager(profile)
        logs = manager.logs(lines=lines)

        return jsonify({"success": True, "logs": logs, "profile": profile})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
