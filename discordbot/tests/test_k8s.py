"""Tests for core/k8s.py — Kubernetes API wrapper module."""

from unittest.mock import MagicMock, patch

import pytest
from kubernetes.client.rest import ApiException

from core.k8s import pod_status, is_pod_running, create_mc_server_pod, delete_mc_server_pod
from core.state import RunState


class TestPodStatus:

    @patch("core.k8s.v1_api")
    def test_running(self, mock_api):
        pod = MagicMock()
        pod.status.phase = "Running"
        mock_api.read_namespaced_pod.return_value = pod

        result = pod_status("mc-server", "test-ns")

        assert result.status == RunState.RUNNING
        mock_api.read_namespaced_pod.assert_called_once_with(
            name="mc-server", namespace="test-ns"
        )

    @patch("core.k8s.v1_api")
    def test_pending(self, mock_api):
        pod = MagicMock()
        pod.status.phase = "Pending"
        mock_api.read_namespaced_pod.return_value = pod

        result = pod_status("mc-server", "test-ns")
        assert result.status == RunState.STARTING

    @patch("core.k8s.v1_api")
    def test_succeeded(self, mock_api):
        pod = MagicMock()
        pod.status.phase = "Succeeded"
        mock_api.read_namespaced_pod.return_value = pod

        result = pod_status("mc-server", "test-ns")
        assert result.status == RunState.EXITED

    @patch("core.k8s.v1_api")
    def test_failed(self, mock_api):
        pod = MagicMock()
        pod.status.phase = "Failed"
        mock_api.read_namespaced_pod.return_value = pod

        result = pod_status("mc-server", "test-ns")
        assert result.status == RunState.DEAD

    @patch("core.k8s.v1_api")
    def test_unknown_phase(self, mock_api):
        pod = MagicMock()
        pod.status.phase = "SomethingWeird"
        mock_api.read_namespaced_pod.return_value = pod

        result = pod_status("mc-server", "test-ns")
        assert result.status == RunState.UNKNOWN
        assert result.extra == {"phase": "somethingweird"}

    @patch("core.k8s.v1_api")
    def test_not_found_returns_none(self, mock_api):
        mock_api.read_namespaced_pod.side_effect = ApiException(status=404)

        result = pod_status("mc-server", "test-ns")
        assert result is None

    @patch("core.k8s.v1_api")
    def test_api_error_returns_unknown(self, mock_api):
        mock_api.read_namespaced_pod.side_effect = ApiException(status=500)

        result = pod_status("mc-server", "test-ns")
        assert result.status == RunState.UNKNOWN

    @patch("core.k8s.v1_api")
    def test_unexpected_error_returns_unknown(self, mock_api):
        mock_api.read_namespaced_pod.side_effect = ConnectionError("timeout")

        result = pod_status("mc-server", "test-ns")
        assert result.status == RunState.UNKNOWN


class TestIsPodRunning:

    @patch("core.k8s.v1_api")
    def test_running_returns_true(self, mock_api):
        pod = MagicMock()
        pod.status.phase = "Running"
        mock_api.read_namespaced_pod.return_value = pod

        assert is_pod_running("mc-server", "test-ns") is True

    @patch("core.k8s.v1_api")
    def test_pending_returns_false(self, mock_api):
        pod = MagicMock()
        pod.status.phase = "Pending"
        mock_api.read_namespaced_pod.return_value = pod

        assert is_pod_running("mc-server", "test-ns") is False

    @patch("core.k8s.v1_api")
    def test_not_found_returns_false(self, mock_api):
        mock_api.read_namespaced_pod.side_effect = ApiException(status=404)

        assert is_pod_running("mc-server", "test-ns") is False


class TestCreateMcServerPod:

    @patch("core.k8s.v1_api")
    def test_success(self, mock_api, k8s_config):
        mock_api.create_namespaced_pod.return_value = MagicMock()

        assert create_mc_server_pod(k8s_config) is True
        mock_api.create_namespaced_pod.assert_called_once()

        # Verify the pod spec
        call_kwargs = mock_api.create_namespaced_pod.call_args
        assert call_kwargs.kwargs["namespace"] == "test-ns"
        pod_body = call_kwargs.kwargs["body"]
        assert pod_body.metadata.name == "mc-server"
        assert pod_body.metadata.labels == {"app": "mc-server"}
        assert pod_body.spec.restart_policy == "Never"

    @patch("core.k8s.v1_api")
    def test_pod_spec_has_correct_volume(self, mock_api, k8s_config):
        mock_api.create_namespaced_pod.return_value = MagicMock()
        create_mc_server_pod(k8s_config)

        pod_body = mock_api.create_namespaced_pod.call_args.kwargs["body"]
        volume = pod_body.spec.volumes[0]
        assert volume.name == "world-data"
        assert volume.persistent_volume_claim.claim_name == "mc-server-data"

    @patch("core.k8s.v1_api")
    def test_pod_spec_has_configmap_env(self, mock_api, k8s_config):
        mock_api.create_namespaced_pod.return_value = MagicMock()
        create_mc_server_pod(k8s_config)

        pod_body = mock_api.create_namespaced_pod.call_args.kwargs["body"]
        container = pod_body.spec.containers[0]
        assert container.env_from[0].config_map_ref.name == "mc-server-config"

    @patch("core.k8s.v1_api")
    def test_pod_spec_has_velero_annotation(self, mock_api, k8s_config):
        mock_api.create_namespaced_pod.return_value = MagicMock()
        create_mc_server_pod(k8s_config)

        pod_body = mock_api.create_namespaced_pod.call_args.kwargs["body"]
        assert pod_body.metadata.annotations["backup.velero.io/backup-volumes"] == "world-data"

    @patch("core.k8s.v1_api")
    def test_pod_spec_has_both_ports(self, mock_api, k8s_config):
        mock_api.create_namespaced_pod.return_value = MagicMock()
        create_mc_server_pod(k8s_config)

        pod_body = mock_api.create_namespaced_pod.call_args.kwargs["body"]
        ports = pod_body.spec.containers[0].ports
        assert len(ports) == 2
        assert ports[0].container_port == 25565
        assert ports[0].protocol == "TCP"
        assert ports[1].container_port == 25565
        assert ports[1].protocol == "UDP"

    @patch("core.k8s.v1_api")
    def test_api_error_returns_false(self, mock_api, k8s_config):
        mock_api.create_namespaced_pod.side_effect = ApiException(status=403)

        assert create_mc_server_pod(k8s_config) is False

    @patch("core.k8s.v1_api")
    def test_conflict_returns_false(self, mock_api, k8s_config):
        mock_api.create_namespaced_pod.side_effect = ApiException(status=409)

        assert create_mc_server_pod(k8s_config) is False

    @patch("core.k8s.v1_api")
    def test_unexpected_error_returns_false(self, mock_api, k8s_config):
        mock_api.create_namespaced_pod.side_effect = RuntimeError("boom")

        assert create_mc_server_pod(k8s_config) is False


class TestDeleteMcServerPod:

    @patch("core.k8s.v1_api")
    def test_success(self, mock_api):
        mock_api.delete_namespaced_pod.return_value = MagicMock()

        assert delete_mc_server_pod("mc-server", "test-ns") is True
        mock_api.delete_namespaced_pod.assert_called_once_with(
            name="mc-server", namespace="test-ns"
        )

    @patch("core.k8s.v1_api")
    def test_not_found_returns_true(self, mock_api):
        """Deleting a pod that doesn't exist is not an error."""
        mock_api.delete_namespaced_pod.side_effect = ApiException(status=404)

        assert delete_mc_server_pod("mc-server", "test-ns") is True

    @patch("core.k8s.v1_api")
    def test_api_error_returns_false(self, mock_api):
        mock_api.delete_namespaced_pod.side_effect = ApiException(status=500)

        assert delete_mc_server_pod("mc-server", "test-ns") is False

    @patch("core.k8s.v1_api")
    def test_unexpected_error_returns_false(self, mock_api):
        mock_api.delete_namespaced_pod.side_effect = RuntimeError("boom")

        assert delete_mc_server_pod("mc-server", "test-ns") is False
