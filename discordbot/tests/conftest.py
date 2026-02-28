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
os.environ.setdefault("KUBERNETES_NAMESPACE", "test-ns")
os.environ.setdefault("KUBERNETES_MC_POD_NAME", "mc-server")
os.environ.setdefault("KUBERNETES_MC_IMAGE", "itzg/minecraft-server:java21")
os.environ.setdefault("KUBERNETES_MC_CONFIGMAP", "mc-server-config")
os.environ.setdefault("KUBERNETES_MC_PVC", "mc-server-data")
os.environ.setdefault("KUBERNETES_MC_PVC_VOLUME_NAME", "world-data")
os.environ.setdefault("LOG_LEVEL", "critical")

# --- Add src to path ---
src_path = os.path.join(os.path.dirname(__file__), "..", "bot", "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# --- Pre-mock kubernetes config (runs at import time in k8s.py) ---
import kubernetes.config as _kube_config

_kube_config.load_incluster_config = MagicMock(
    side_effect=_kube_config.ConfigException("test")
)
_kube_config.load_kube_config = MagicMock()

# --- Fixtures ---
import pytest


@pytest.fixture
def k8s_config():
    from core.config import KubernetesConfig

    return KubernetesConfig(
        namespace="test-ns",
        mc_pod_name="mc-server",
        mc_image="itzg/minecraft-server:java21",
        mc_configmap_name="mc-server-config",
        mc_pvc_name="mc-server-data",
        mc_pvc_volume_name="world-data",
    )


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
