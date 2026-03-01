"""
Minimal HTTP server for MC server pod management.

Usage:
    DEPLOYMENT=kubernetes HTTP_API_TOKEN=mysecret python http_server.py

Endpoints:
    GET  /k8s/start   - Create the MC server pod (or clean up old one first)
    GET  /k8s/stop    - Delete the MC server pod
    GET  /k8s/status  - Get MC server pod status

All endpoints require a Bearer token via the Authorization header when
HTTP_API_TOKEN is set.
"""

import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

from core.service import get_service, StartOutcome


service = get_service()

API_TOKEN = os.getenv("HTTP_API_TOKEN")


class K8sHTTPHandler(BaseHTTPRequestHandler):

    def _respond(self, status_code, body):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def _check_auth(self):
        if not API_TOKEN:
            return True
        auth = self.headers.get("Authorization", "")
        if auth == f"Bearer {API_TOKEN}":
            return True
        self._respond(401, {"error": "Unauthorized"})
        return False

    def do_GET(self):
        if not self._check_auth():
            return

        path = self.path.rstrip("/")

        if path == "/k8s/start":
            self._handle_start()
        elif path == "/k8s/stop":
            self._handle_stop()
        elif path == "/k8s/status":
            self._handle_status()
        else:
            self._respond(404, {"error": "Not found. Use /k8s/start, /k8s/stop, or /k8s/status"})

    def _handle_start(self):
        result = service.start()
        outcome = result.outcome

        if outcome == StartOutcome.STARTED:
            self._respond(200, {"action": "created", "success": True})
        elif outcome == StartOutcome.ALREADY_RUNNING:
            self._respond(200, {"action": "none", "message": "Already running"})
        elif outcome == StartOutcome.ALREADY_STARTING:
            self._respond(200, {"action": "none", "message": "Already starting"})
        elif outcome == StartOutcome.FAILED:
            self._respond(500, {"action": "created", "success": False, "message": result.message})
        elif outcome == StartOutcome.ERROR:
            self._respond(500, {"action": "error", "success": False, "message": result.message})

    def _handle_stop(self):
        result = service.stop()
        self._respond(200 if result.success else 500, {
            "action": "deleted",
            "success": result.success,
        })

    def _handle_status(self):
        result = service.status()
        if result.run_state is None:
            self._respond(200, {"status": "not_found"})
        else:
            self._respond(200, {"status": result.run_state.value})


if __name__ == "__main__":
    port = 8080
    server = HTTPServer(("0.0.0.0", port), K8sHTTPHandler)
    print(f"Test server listening on :{port}")
    print(f"Endpoints: /k8s/start  /k8s/stop  /k8s/status")
    server.serve_forever()
