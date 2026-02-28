"""Tests for handler.py — KubernetesHandler, LocalHandler, AwsEc2Handler."""

import subprocess
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.state import RunState
from core.k8s import PodStatus
import handler as handler_module
from handler import KubernetesHandler, LocalHandler, AwsEc2Handler, get_handler


# ---------------------------------------------------------------------------
# KubernetesHandler
# ---------------------------------------------------------------------------


class TestKubernetesHandler:

    @pytest.fixture
    def k8s_handler(self, mock_bot):
        return KubernetesHandler(mock_bot)

    @pytest.mark.asyncio
    @patch("handler.k8s")
    @patch.object(KubernetesHandler, "_finalize_server_start", new_callable=AsyncMock)
    @patch("handler.state_manager")
    async def test_start_creates_pod_when_not_found(
        self, mock_state, mock_finalize, mock_k8s, k8s_handler, mock_ctx
    ):
        mock_k8s.pod_status.return_value = None
        mock_k8s.create_mc_server_pod.return_value = True

        await k8s_handler.start(mock_ctx)

        mock_state.reset.assert_called_once()
        mock_k8s.create_mc_server_pod.assert_called_once()
        mock_finalize.assert_called_once_with(mock_ctx)

    @pytest.mark.asyncio
    @patch("handler.k8s")
    @patch("handler.state_manager")
    async def test_start_responds_already_running(
        self, mock_state, mock_k8s, k8s_handler, mock_ctx
    ):
        mock_k8s.pod_status.return_value = PodStatus(RunState.RUNNING)

        await k8s_handler.start(mock_ctx)

        mock_ctx.respond.assert_called_once()
        call_args = mock_ctx.respond.call_args
        assert "already running" in str(call_args).lower()
        mock_k8s.create_mc_server_pod.assert_not_called()

    @pytest.mark.asyncio
    @patch("handler.k8s")
    @patch("handler.state_manager")
    async def test_start_responds_already_starting(
        self, mock_state, mock_k8s, k8s_handler, mock_ctx
    ):
        mock_k8s.pod_status.return_value = PodStatus(RunState.STARTING)

        await k8s_handler.start(mock_ctx)

        mock_ctx.respond.assert_called_once()
        call_args = mock_ctx.respond.call_args
        assert "already starting" in str(call_args).lower()

    @pytest.mark.asyncio
    @patch("handler.k8s")
    @patch.object(KubernetesHandler, "_finalize_server_start", new_callable=AsyncMock)
    @patch("handler.state_manager")
    async def test_start_recreates_pod_when_exited(
        self, mock_state, mock_finalize, mock_k8s, k8s_handler, mock_ctx
    ):
        mock_k8s.pod_status.return_value = PodStatus(RunState.EXITED)
        mock_k8s.create_mc_server_pod.return_value = True

        await k8s_handler.start(mock_ctx)

        mock_k8s.delete_mc_server_pod.assert_called_once()
        mock_state.reset.assert_called_once()
        mock_k8s.create_mc_server_pod.assert_called_once()
        mock_finalize.assert_called_once_with(mock_ctx)

    @pytest.mark.asyncio
    @patch("handler.k8s")
    @patch.object(KubernetesHandler, "_finalize_server_start", new_callable=AsyncMock)
    @patch("handler.state_manager")
    async def test_start_recreates_pod_when_dead(
        self, mock_state, mock_finalize, mock_k8s, k8s_handler, mock_ctx
    ):
        mock_k8s.pod_status.return_value = PodStatus(RunState.DEAD)
        mock_k8s.create_mc_server_pod.return_value = True

        await k8s_handler.start(mock_ctx)

        mock_k8s.delete_mc_server_pod.assert_called_once()
        mock_k8s.create_mc_server_pod.assert_called_once()
        mock_finalize.assert_called_once_with(mock_ctx)

    @pytest.mark.asyncio
    @patch("handler.k8s")
    @patch.object(KubernetesHandler, "_finalize_server_start", new_callable=AsyncMock)
    @patch("handler.state_manager")
    async def test_start_recreates_pod_when_unknown(
        self, mock_state, mock_finalize, mock_k8s, k8s_handler, mock_ctx
    ):
        mock_k8s.pod_status.return_value = PodStatus(RunState.UNKNOWN)
        mock_k8s.create_mc_server_pod.return_value = True

        await k8s_handler.start(mock_ctx)

        mock_k8s.delete_mc_server_pod.assert_called_once()
        mock_k8s.create_mc_server_pod.assert_called_once()

    @pytest.mark.asyncio
    @patch("handler.k8s")
    @patch("handler.state_manager")
    async def test_start_responds_error_when_create_fails(
        self, mock_state, mock_k8s, k8s_handler, mock_ctx
    ):
        mock_k8s.pod_status.return_value = None
        mock_k8s.create_mc_server_pod.return_value = False

        await k8s_handler.start(mock_ctx)

        mock_ctx.respond.assert_called_once()
        call_args = mock_ctx.respond.call_args
        assert "failed" in str(call_args).lower() or "cry" in str(call_args).lower()

    @pytest.mark.asyncio
    @patch("handler.k8s")
    @patch("handler.state_manager")
    async def test_start_handles_exception(
        self, mock_state, mock_k8s, k8s_handler, mock_ctx
    ):
        mock_k8s.pod_status.side_effect = RuntimeError("k8s API down")

        await k8s_handler.start(mock_ctx)

        mock_ctx.respond.assert_called_once()

    @pytest.mark.asyncio
    async def test_ip(self, k8s_handler, mock_ctx):
        await k8s_handler.ip(mock_ctx)

        mock_ctx.respond.assert_called_once()
        assert "kubernetes" in str(mock_ctx.respond.call_args).lower()


# ---------------------------------------------------------------------------
# LocalHandler
# ---------------------------------------------------------------------------


class TestLocalHandler:

    @pytest.fixture(autouse=True)
    def _inject_docker_util(self):
        """Inject mock docker_util into handler module (not imported in K8s mode)."""
        self.mock_docker_util = MagicMock()
        handler_module.docker_util = self.mock_docker_util
        yield
        if hasattr(handler_module, "docker_util"):
            delattr(handler_module, "docker_util")

    @pytest.fixture
    def local_handler(self, mock_bot):
        return LocalHandler(mock_bot)

    @pytest.mark.asyncio
    @patch("handler.state_manager")
    async def test_start_responds_already_running(
        self, mock_state, local_handler, mock_ctx
    ):
        self.mock_docker_util.is_container_running.return_value = True

        await local_handler.start(mock_ctx)

        mock_ctx.respond.assert_called_once()
        assert "already running" in str(mock_ctx.respond.call_args).lower()

    @pytest.mark.asyncio
    @patch("subprocess.run")
    @patch.object(LocalHandler, "_finalize_server_start", new_callable=AsyncMock)
    @patch("handler.state_manager")
    async def test_start_runs_docker_compose(
        self, mock_state, mock_finalize, mock_subprocess, local_handler, mock_ctx
    ):
        self.mock_docker_util.is_container_running.return_value = False

        await local_handler.start(mock_ctx)

        mock_state.reset.assert_called_once()
        # docker compose down then up
        assert mock_subprocess.call_count == 2
        down_call = mock_subprocess.call_args_list[0]
        assert "down" in down_call.args[0]
        up_call = mock_subprocess.call_args_list[1]
        assert "up" in up_call.args[0]
        mock_finalize.assert_called_once_with(mock_ctx)

    @pytest.mark.asyncio
    @patch("subprocess.run")
    @patch("handler.state_manager")
    async def test_start_responds_error_on_docker_failure(
        self, mock_state, mock_subprocess, local_handler, mock_ctx
    ):
        self.mock_docker_util.is_container_running.return_value = False
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            1, "docker compose", stderr="container failed"
        )

        await local_handler.start(mock_ctx)

        mock_ctx.respond.assert_called_once()
        assert "failed" in str(mock_ctx.respond.call_args).lower()

    @pytest.mark.asyncio
    async def test_ip(self, local_handler, mock_ctx):
        await local_handler.ip(mock_ctx)

        mock_ctx.respond.assert_called_once()
        assert "locally" in str(mock_ctx.respond.call_args).lower()


# ---------------------------------------------------------------------------
# AwsEc2Handler
# ---------------------------------------------------------------------------


class TestAwsEc2Handler:

    @pytest.fixture(autouse=True)
    def _inject_ec2(self):
        """Inject mock ec2 into handler module (not imported in K8s mode)."""
        self.mock_ec2 = MagicMock()
        handler_module.ec2 = self.mock_ec2
        yield
        if hasattr(handler_module, "ec2"):
            delattr(handler_module, "ec2")

    @pytest.fixture
    def ec2_handler(self, mock_bot):
        return AwsEc2Handler(mock_bot)

    @pytest.mark.asyncio
    @patch("handler.state_manager")
    async def test_start_responds_error_on_fleet_failure(
        self, mock_state, ec2_handler, mock_ctx
    ):
        instance = MagicMock()
        instance.errors = ["InsufficientCapacity"]
        self.mock_ec2.startServer.return_value = instance

        await ec2_handler.start(mock_ctx)

        mock_ctx.respond.assert_called_once()
        assert "error" in str(mock_ctx.respond.call_args).lower()

    @pytest.mark.asyncio
    @patch("handler.state_manager")
    async def test_start_responds_already_running(
        self, mock_state, ec2_handler, mock_ctx
    ):
        instance = MagicMock()
        instance.errors = []
        instance.isNew = False
        self.mock_ec2.startServer.return_value = instance

        await ec2_handler.start(mock_ctx)

        mock_ctx.respond.assert_called_once()
        assert "already running" in str(mock_ctx.respond.call_args).lower()

    @pytest.mark.asyncio
    @patch.object(AwsEc2Handler, "_finalize_server_start", new_callable=AsyncMock)
    @patch("handler.state_manager")
    async def test_start_new_server(
        self, mock_state, mock_finalize, ec2_handler, mock_ctx
    ):
        instance = MagicMock()
        instance.errors = []
        instance.isNew = True
        self.mock_ec2.startServer.return_value = instance

        await ec2_handler.start(mock_ctx)

        mock_state.reset.assert_called_once()
        mock_state.set_ec2_instance.assert_called_once_with(instance)
        mock_finalize.assert_called_once_with(mock_ctx)

    @pytest.mark.asyncio
    async def test_ip_returns_public_ip(self, ec2_handler, mock_ctx):
        instance = MagicMock()
        instance.publicIp = "1.2.3.4"
        self.mock_ec2.getServerInstance.return_value = instance

        await ec2_handler.ip(mock_ctx)

        mock_ctx.respond.assert_called_once()
        assert "1.2.3.4" in str(mock_ctx.respond.call_args)

    @pytest.mark.asyncio
    async def test_ip_returns_unknown_when_no_instance(self, ec2_handler, mock_ctx):
        self.mock_ec2.getServerInstance.return_value = None

        await ec2_handler.ip(mock_ctx)

        mock_ctx.respond.assert_called_once()
        assert "unknown" in str(mock_ctx.respond.call_args).lower()


# ---------------------------------------------------------------------------
# Handler Factory
# ---------------------------------------------------------------------------


class TestGetHandler:

    @patch("handler.config")
    def test_returns_kubernetes_handler(self, mock_config, mock_bot):
        from core.config import Deployment

        mock_config.GENERAL.deployment = Deployment.KUBERNETES
        result = get_handler(mock_bot)
        assert isinstance(result, KubernetesHandler)

    @patch("handler.config")
    def test_returns_local_handler(self, mock_config, mock_bot):
        from core.config import Deployment

        mock_config.GENERAL.deployment = Deployment.LOCAL
        result = get_handler(mock_bot)
        assert isinstance(result, LocalHandler)

    @patch("handler.config")
    def test_returns_ec2_handler(self, mock_config, mock_bot):
        from core.config import Deployment

        mock_config.GENERAL.deployment = Deployment.AWS_EC2
        result = get_handler(mock_bot)
        assert isinstance(result, AwsEc2Handler)
