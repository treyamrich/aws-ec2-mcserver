"""Tests for core/service.py — KubernetesService, LocalService, AwsEc2Service."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from conftest import SAMPLE_POD_TEMPLATE
from core.state import RunState
from k8s import PodStatus, PodTemplate
from core.service import (
    KubernetesService,
    LocalService,
    AwsEc2Service,
    StartOutcome,
    get_service,
)


# ---------------------------------------------------------------------------
# KubernetesService
# ---------------------------------------------------------------------------


class TestKubernetesService:

    @pytest.fixture
    def k8s_service(self):
        with patch.object(PodTemplate, "from_file", return_value=PodTemplate(SAMPLE_POD_TEMPLATE)):
            svc = KubernetesService()
        return svc

    @patch("core.service.state_manager")
    def test_start_creates_pod_when_not_found(self, mock_state, k8s_service):
        k8s_service._k8s = MagicMock()
        k8s_service._k8s.pod_status.return_value = None
        k8s_service._k8s.create_pod.return_value = True

        result = k8s_service.start()

        assert result.outcome == StartOutcome.STARTED
        mock_state.reset.assert_called_once()
        k8s_service._k8s.create_pod.assert_called_once()
        mock_state.set_server_state_running.assert_called_once()

    @patch("core.service.state_manager")
    def test_start_already_running(self, mock_state, k8s_service):
        k8s_service._k8s = MagicMock()
        k8s_service._k8s.pod_status.return_value = PodStatus(RunState.RUNNING)

        result = k8s_service.start()

        assert result.outcome == StartOutcome.ALREADY_RUNNING
        k8s_service._k8s.create_pod.assert_not_called()

    @patch("core.service.state_manager")
    def test_start_already_starting(self, mock_state, k8s_service):
        k8s_service._k8s = MagicMock()
        k8s_service._k8s.pod_status.return_value = PodStatus(RunState.STARTING)

        result = k8s_service.start()

        assert result.outcome == StartOutcome.ALREADY_STARTING

    @pytest.mark.parametrize("state", [RunState.EXITED, RunState.DEAD, RunState.UNKNOWN])
    @patch("core.service.state_manager")
    def test_start_recreates_pod_on_terminal_state(self, mock_state, k8s_service, state):
        k8s_service._k8s = MagicMock()
        k8s_service._k8s.pod_status.return_value = PodStatus(state)
        k8s_service._k8s.create_pod.return_value = True

        result = k8s_service.start()

        assert result.outcome == StartOutcome.STARTED
        k8s_service._k8s.delete_pod.assert_called_once()
        k8s_service._k8s.create_pod.assert_called_once()
        mock_state.reset.assert_called_once()

    @patch("core.service.state_manager")
    def test_start_fails_when_create_fails(self, mock_state, k8s_service):
        k8s_service._k8s = MagicMock()
        k8s_service._k8s.pod_status.return_value = None
        k8s_service._k8s.create_pod.return_value = False

        result = k8s_service.start()

        assert result.outcome == StartOutcome.FAILED

    @patch("core.service.state_manager")
    def test_start_returns_error_on_exception(self, mock_state, k8s_service):
        k8s_service._k8s = MagicMock()
        k8s_service._k8s.pod_status.side_effect = RuntimeError("k8s API down")

        result = k8s_service.start()

        assert result.outcome == StartOutcome.ERROR
        assert "k8s API down" in result.message

    def test_stop(self, k8s_service):
        k8s_service._k8s = MagicMock()
        k8s_service._k8s.delete_pod.return_value = True

        result = k8s_service.stop()

        assert result.success is True
        k8s_service._k8s.delete_pod.assert_called_once()

    def test_stop_failure(self, k8s_service):
        k8s_service._k8s = MagicMock()
        k8s_service._k8s.delete_pod.return_value = False

        result = k8s_service.stop()

        assert result.success is False

    def test_status_not_found(self, k8s_service):
        k8s_service._k8s = MagicMock()
        k8s_service._k8s.pod_status.return_value = None

        result = k8s_service.status()

        assert result.run_state is None
        assert result.message == "not_found"

    def test_status_running(self, k8s_service):
        k8s_service._k8s = MagicMock()
        k8s_service._k8s.pod_status.return_value = PodStatus(RunState.RUNNING)

        result = k8s_service.status()

        assert result.run_state == RunState.RUNNING

    def test_ip(self, k8s_service):
        result = k8s_service.ip()

        assert result.ip is None
        assert "kubernetes" in result.message.lower()


# ---------------------------------------------------------------------------
# LocalService
# ---------------------------------------------------------------------------


class TestLocalService:

    @pytest.fixture
    def local_service(self):
        svc = LocalService.__new__(LocalService)
        svc._docker_util = MagicMock()
        return svc

    @patch("core.service.state_manager")
    def test_start_already_running(self, mock_state, local_service):
        local_service._docker_util.is_container_running.return_value = True

        result = local_service.start()

        assert result.outcome == StartOutcome.ALREADY_RUNNING

    @patch("subprocess.run")
    @patch("core.service.state_manager")
    def test_start_runs_docker_compose(self, mock_state, mock_subprocess, local_service):
        local_service._docker_util.is_container_running.return_value = False

        result = local_service.start()

        assert result.outcome == StartOutcome.STARTED
        mock_state.reset.assert_called_once()
        assert mock_subprocess.call_count == 2
        down_call = mock_subprocess.call_args_list[0]
        assert "down" in down_call.args[0]
        up_call = mock_subprocess.call_args_list[1]
        assert "up" in up_call.args[0]
        mock_state.set_server_state_running.assert_called_once()

    @patch("subprocess.run")
    @patch("core.service.state_manager")
    def test_start_fails_on_docker_error(self, mock_state, mock_subprocess, local_service):
        local_service._docker_util.is_container_running.return_value = False
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            1, "docker compose", stderr="container failed"
        )

        result = local_service.start()

        assert result.outcome == StartOutcome.FAILED

    @patch("subprocess.run")
    def test_stop_success(self, mock_subprocess, local_service):
        result = local_service.stop()

        assert result.success is True
        mock_subprocess.assert_called_once()

    @patch("subprocess.run")
    def test_stop_failure(self, mock_subprocess, local_service):
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            1, "docker compose", stderr="error"
        )

        result = local_service.stop()

        assert result.success is False

    def test_ip(self, local_service):
        result = local_service.ip()

        assert result.ip is None
        assert "locally" in result.message.lower()


# ---------------------------------------------------------------------------
# AwsEc2Service
# ---------------------------------------------------------------------------


class TestAwsEc2Service:

    @pytest.fixture
    def ec2_service(self):
        svc = AwsEc2Service.__new__(AwsEc2Service)
        svc._ec2 = MagicMock()
        return svc

    @patch("core.service.state_manager")
    def test_start_fails_on_fleet_error(self, mock_state, ec2_service):
        instance = MagicMock()
        instance.errors = ["InsufficientCapacity"]
        ec2_service._ec2.startServer.return_value = instance

        result = ec2_service.start()

        assert result.outcome == StartOutcome.FAILED

    @patch("core.service.state_manager")
    def test_start_already_running(self, mock_state, ec2_service):
        instance = MagicMock()
        instance.errors = []
        instance.isNew = False
        ec2_service._ec2.startServer.return_value = instance

        result = ec2_service.start()

        assert result.outcome == StartOutcome.ALREADY_RUNNING

    @patch("core.service.state_manager")
    def test_start_new_server(self, mock_state, ec2_service):
        instance = MagicMock()
        instance.errors = []
        instance.isNew = True
        ec2_service._ec2.startServer.return_value = instance

        result = ec2_service.start()

        assert result.outcome == StartOutcome.STARTED
        mock_state.reset.assert_called_once()
        mock_state.set_ec2_instance.assert_called_once_with(instance)
        mock_state.set_server_state_running.assert_called_once()

    def test_ip_returns_public_ip(self, ec2_service):
        instance = MagicMock()
        instance.publicIp = "1.2.3.4"
        ec2_service._ec2.getServerInstance.return_value = instance

        result = ec2_service.ip()

        assert result.ip == "1.2.3.4"
        assert "1.2.3.4" in result.message

    def test_ip_returns_none_when_no_instance(self, ec2_service):
        ec2_service._ec2.getServerInstance.return_value = None

        result = ec2_service.ip()

        assert result.ip is None


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


class TestGetService:

    @patch("core.service.config")
    def test_returns_kubernetes_service(self, mock_config):
        from core.config import Deployment

        mock_config.GENERAL.deployment = Deployment.KUBERNETES
        mock_config.KUBERNETES.pod_template_path = "/config/pod-template.json"
        with patch.object(PodTemplate, "from_file", return_value=PodTemplate(SAMPLE_POD_TEMPLATE)):
            result = get_service()
        assert isinstance(result, KubernetesService)

    @patch("core.service.config")
    def test_returns_local_service(self, mock_config):
        import sys
        from core.config import Deployment

        mock_config.GENERAL.deployment = Deployment.LOCAL
        # docker module isn't installed in test env, so mock it at sys.modules level
        sys.modules.setdefault("docker", MagicMock())
        try:
            result = get_service()
            assert isinstance(result, LocalService)
        finally:
            sys.modules.pop("docker", None)

    @patch("core.service.config")
    def test_returns_ec2_service(self, mock_config):
        from core.config import Deployment

        mock_config.GENERAL.deployment = Deployment.AWS_EC2
        result = get_service()
        assert isinstance(result, AwsEc2Service)
