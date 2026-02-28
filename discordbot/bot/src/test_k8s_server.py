"""
Minimal HTTP test server for Kubernetes MC server pod management.
Mimics what the Discord bot's KubernetesHandler does without Discord, Vault, or auth.

Usage:
    DEPLOYMENT=kubernetes KUBERNETES_NAMESPACE=minecraft python test_k8s_server.py

Endpoints:
    GET  /start   - Create the MC server pod (or clean up old one first)
    GET  /stop    - Delete the MC server pod
    GET  /status  - Get MC server pod status
"""

import json
from http.server import HTTPServer, BaseHTTPRequestHandler

from core.config import config
from core import k8s
from core.state import RunState


class Handler(BaseHTTPRequestHandler):

    def _respond(self, status_code, body):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def do_GET(self):
        path = self.path.rstrip("/")
        k8s_config = config.KUBERNETES

        if path == "/start":
            self._handle_start(k8s_config)
        elif path == "/stop":
            self._handle_stop(k8s_config)
        elif path == "/status":
            self._handle_status(k8s_config)
        else:
            self._respond(404, {"error": "Not found. Use /start, /stop, or /status"})

    def _handle_start(self, k8s_config):
        status = k8s.pod_status(k8s_config.mc_pod_name, k8s_config.namespace)

        if status is None:
            ok = k8s.create_mc_server_pod(k8s_config)
            self._respond(200 if ok else 500, {
                "action": "created",
                "success": ok,
            })

        elif status.status == RunState.RUNNING:
            self._respond(200, {"action": "none", "message": "Already running"})

        elif status.status == RunState.STARTING:
            self._respond(200, {"action": "none", "message": "Already starting"})

        elif status.status in (RunState.EXITED, RunState.DEAD, RunState.UNKNOWN):
            k8s.delete_mc_server_pod(k8s_config.mc_pod_name, k8s_config.namespace)
            ok = k8s.create_mc_server_pod(k8s_config)
            self._respond(200 if ok else 500, {
                "action": "recreated",
                "previous_state": status.status.value,
                "success": ok,
            })

    def _handle_stop(self, k8s_config):
        ok = k8s.delete_mc_server_pod(k8s_config.mc_pod_name, k8s_config.namespace)
        self._respond(200 if ok else 500, {"action": "deleted", "success": ok})

    def _handle_status(self, k8s_config):
        status = k8s.pod_status(k8s_config.mc_pod_name, k8s_config.namespace)
        if status is None:
            self._respond(200, {"status": "not_found"})
        else:
            self._respond(200, {"status": status.status.value})


if __name__ == "__main__":
    port = 8080
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"Test server listening on :{port}")
    print(f"  Namespace: {config.KUBERNETES.namespace}")
    print(f"  Pod name:  {config.KUBERNETES.mc_pod_name}")
    print(f"  Image:     {config.KUBERNETES.mc_image}")
    print(f"Endpoints: /start  /stop  /status")
    server.serve_forever()
