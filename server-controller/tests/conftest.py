"""
Test configuration — handles module-level side effects before app code imports.

The app has aggressive module-level initialization (config singleton, kubernetes
config loading, mcstatus server creation). This conftest sets up env vars and
mocks BEFORE any application modules are imported by test files.
"""

import os
import sys
from unittest.mock import MagicMock

# --- Environment variables (must be set before any app imports) ---
os.environ.setdefault("DEPLOYMENT", "kubernetes")
os.environ.setdefault("SERVER_ADDRESS", "test-server")
os.environ.setdefault("SERVER_STATUS_HOST", "test-server")
os.environ.setdefault("SERVER_TYPE", "java")
os.environ.setdefault("SERVER_PORT_JAVA", "25565")
os.environ.setdefault("LOG_LEVEL", "critical")

# --- Add src to path ---
src_path = os.path.join(os.path.dirname(__file__), "..", "bot", "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# --- Pre-mock kubernetes config (runs at import time in k8s/client.py) ---
import kubernetes.config as _kube_config

_kube_config.load_incluster_config = MagicMock(
    side_effect=_kube_config.ConfigException("test")
)
_kube_config.load_kube_config = MagicMock()

# --- Fixtures ---
import pytest

from k8s import PodTemplate


SAMPLE_POD_TEMPLATE = {
    "metadata": {
        "name": "mc-server",
        "namespace": "test-ns",
        "labels": {"app": "mc-server"},
        "annotations": {"backup.velero.io/backup-volumes": "world-data"},
    },
    "spec": {
        "restartPolicy": "Never",
        "containers": [
            {
                "name": "mc-server",
                "image": "itzg/minecraft-server:java21",
                "ports": [
                    {"containerPort": 25565, "hostPort": 25565, "protocol": "TCP"},
                    {"containerPort": 25565, "hostPort": 25565, "protocol": "UDP"},
                ],
                "envFrom": [{"configMapRef": {"name": "mc-server-config"}}],
                "volumeMounts": [{"name": "world-data", "mountPath": "/data"}],
            }
        ],
        "volumes": [
            {
                "name": "world-data",
                "persistentVolumeClaim": {"claimName": "mc-server-data"},
            }
        ],
    },
}


@pytest.fixture
def pod_template():
    return PodTemplate(SAMPLE_POD_TEMPLATE)


@pytest.fixture
def mock_ctx():
    """Mock Discord ApplicationContext."""
    ctx = MagicMock()
    ctx.guild.name = "Test Guild"
    ctx.channel_id = 123456

    async def mock_respond(*args, **kwargs):
        resp = MagicMock()
        resp.id = 999
        return resp

    ctx.respond = MagicMock(side_effect=mock_respond)
    return ctx


@pytest.fixture
def mock_bot():
    bot = MagicMock()
    bot.latency = 0.05
    return bot
