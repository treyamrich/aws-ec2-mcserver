"""Tests for k8s/ — Kubernetes API wrapper module."""

from unittest.mock import MagicMock, patch

import pytest
from kubernetes.client.rest import ApiException

from k8s import PodTemplate, pod_status, is_pod_running, create_pod, delete_pod
from k8s.client import PodStatus
from core.state import RunState


class TestPodTemplate:

    def test_extracts_name(self, pod_template):
        assert pod_template.pod_name == "mc-server"

    def test_extracts_namespace(self, pod_template):
        assert pod_template.namespace == "test-ns"

    def test_defaults_namespace_to_default(self):
        tpl = PodTemplate({"metadata": {"name": "my-pod"}})
        assert tpl.namespace == "default"

    def test_stores_full_template(self, pod_template):
        assert "spec" in pod_template.template
        assert pod_template.template["spec"]["restartPolicy"] == "Never"

    @patch("builtins.open", create=True)
    @patch("json.load")
    def test_from_file(self, mock_json_load, mock_open):
        mock_json_load.return_value = {
            "metadata": {"name": "mc-server", "namespace": "test-ns"}
        }
        pt = PodTemplate.from_file("/config/pod-template.json")
        assert pt.pod_name == "mc-server"
        assert pt.namespace == "test-ns"


class TestPodStatus:

    @patch("k8s.client.v1_api")
    def test_running(self, mock_api):
        pod = MagicMock()
        pod.status.phase = "Running"
        mock_api.read_namespaced_pod.return_value = pod

        result = pod_status("mc-server", "test-ns")

        assert result.status == RunState.RUNNING
        mock_api.read_namespaced_pod.assert_called_once_with(
            name="mc-server", namespace="test-ns"
        )

    @patch("k8s.client.v1_api")
    def test_pending(self, mock_api):
        pod = MagicMock()
        pod.status.phase = "Pending"
        mock_api.read_namespaced_pod.return_value = pod

        result = pod_status("mc-server", "test-ns")
        assert result.status == RunState.STARTING

    @patch("k8s.client.v1_api")
    def test_succeeded(self, mock_api):
        pod = MagicMock()
        pod.status.phase = "Succeeded"
        mock_api.read_namespaced_pod.return_value = pod

        result = pod_status("mc-server", "test-ns")
        assert result.status == RunState.EXITED

    @patch("k8s.client.v1_api")
    def test_failed(self, mock_api):
        pod = MagicMock()
        pod.status.phase = "Failed"
        mock_api.read_namespaced_pod.return_value = pod

        result = pod_status("mc-server", "test-ns")
        assert result.status == RunState.DEAD

    @patch("k8s.client.v1_api")
    def test_unknown_phase(self, mock_api):
        pod = MagicMock()
        pod.status.phase = "SomethingWeird"
        mock_api.read_namespaced_pod.return_value = pod

        result = pod_status("mc-server", "test-ns")
        assert result.status == RunState.UNKNOWN
        assert result.extra == {"phase": "somethingweird"}

    @patch("k8s.client.v1_api")
    def test_not_found_returns_none(self, mock_api):
        mock_api.read_namespaced_pod.side_effect = ApiException(status=404)

        result = pod_status("mc-server", "test-ns")
        assert result is None

    @patch("k8s.client.v1_api")
    def test_api_error_returns_unknown(self, mock_api):
        mock_api.read_namespaced_pod.side_effect = ApiException(status=500)

        result = pod_status("mc-server", "test-ns")
        assert result.status == RunState.UNKNOWN

    @patch("k8s.client.v1_api")
    def test_unexpected_error_returns_unknown(self, mock_api):
        mock_api.read_namespaced_pod.side_effect = ConnectionError("timeout")

        result = pod_status("mc-server", "test-ns")
        assert result.status == RunState.UNKNOWN


class TestIsPodRunning:

    @patch("k8s.client.v1_api")
    def test_running_returns_true(self, mock_api):
        pod = MagicMock()
        pod.status.phase = "Running"
        mock_api.read_namespaced_pod.return_value = pod

        assert is_pod_running("mc-server", "test-ns") is True

    @patch("k8s.client.v1_api")
    def test_pending_returns_false(self, mock_api):
        pod = MagicMock()
        pod.status.phase = "Pending"
        mock_api.read_namespaced_pod.return_value = pod

        assert is_pod_running("mc-server", "test-ns") is False

    @patch("k8s.client.v1_api")
    def test_not_found_returns_false(self, mock_api):
        mock_api.read_namespaced_pod.side_effect = ApiException(status=404)

        assert is_pod_running("mc-server", "test-ns") is False


class TestCreatePod:

    @patch("k8s.client.v1_api")
    def test_success(self, mock_api, pod_template):
        mock_api.create_namespaced_pod.return_value = MagicMock()

        assert create_pod(pod_template) is True
        mock_api.create_namespaced_pod.assert_called_once_with(
            namespace="test-ns", body=pod_template.template
        )

    @patch("k8s.client.v1_api")
    def test_passes_full_template_as_body(self, mock_api, pod_template):
        mock_api.create_namespaced_pod.return_value = MagicMock()
        create_pod(pod_template)

        call_kwargs = mock_api.create_namespaced_pod.call_args.kwargs
        body = call_kwargs["body"]
        assert body["metadata"]["name"] == "mc-server"
        assert body["spec"]["restartPolicy"] == "Never"
        assert body["spec"]["containers"][0]["image"] == "itzg/minecraft-server:java21"

    @patch("k8s.client.v1_api")
    def test_api_error_returns_false(self, mock_api, pod_template):
        mock_api.create_namespaced_pod.side_effect = ApiException(status=403)

        assert create_pod(pod_template) is False

    @patch("k8s.client.v1_api")
    def test_conflict_returns_false(self, mock_api, pod_template):
        mock_api.create_namespaced_pod.side_effect = ApiException(status=409)

        assert create_pod(pod_template) is False

    @patch("k8s.client.v1_api")
    def test_unexpected_error_returns_false(self, mock_api, pod_template):
        mock_api.create_namespaced_pod.side_effect = RuntimeError("boom")

        assert create_pod(pod_template) is False


class TestDeletePod:

    @patch("k8s.client.v1_api")
    def test_success(self, mock_api):
        mock_api.delete_namespaced_pod.return_value = MagicMock()

        assert delete_pod("mc-server", "test-ns") is True
        mock_api.delete_namespaced_pod.assert_called_once_with(
            name="mc-server", namespace="test-ns"
        )

    @patch("k8s.client.v1_api")
    def test_not_found_returns_true(self, mock_api):
        """Deleting a pod that doesn't exist is not an error."""
        mock_api.delete_namespaced_pod.side_effect = ApiException(status=404)

        assert delete_pod("mc-server", "test-ns") is True

    @patch("k8s.client.v1_api")
    def test_api_error_returns_false(self, mock_api):
        mock_api.delete_namespaced_pod.side_effect = ApiException(status=500)

        assert delete_pod("mc-server", "test-ns") is False

    @patch("k8s.client.v1_api")
    def test_unexpected_error_returns_false(self, mock_api):
        mock_api.delete_namespaced_pod.side_effect = RuntimeError("boom")

        assert delete_pod("mc-server", "test-ns") is False
