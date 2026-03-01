
import json
import os
from typing import Optional

from kubernetes import client, config as kube_config
from kubernetes.client.rest import ApiException

from core.logger import Logger
from core.state import RunState

logger = Logger(os.path.basename(__file__))


def _load_kube_config():
    # In-cluster auth uses the pod's service account token. RBAC must be configured to grant the SA permissions to manage pods.
    try:
        kube_config.load_incluster_config()
        logger.info("Loaded in-cluster Kubernetes config.")
    except kube_config.ConfigException:
        try:
            kube_config.load_kube_config()
            logger.info("Loaded local kubeconfig.")
        except kube_config.ConfigException:
            raise RuntimeError("Could not load Kubernetes config (neither in-cluster nor local kubeconfig).")


_load_kube_config()
v1_api = client.CoreV1Api()


class PodTemplate:
    """Loaded pod template with extracted metadata for lifecycle management."""

    def __init__(self, template: dict):
        self.template = template
        metadata = template.get("metadata", {})
        self.pod_name = metadata.get("name")
        self.namespace = metadata.get("namespace", "default")

    @staticmethod
    def from_file(path: str) -> 'PodTemplate':
        with open(path) as f:
            template = json.load(f)
        logger.info(f"Loaded pod template from '{path}'.")
        return PodTemplate(template)


class PodStatus:
    def __init__(self, status: RunState, extra: Optional[dict] = None):
        self.status = status
        self.extra = extra

    @staticmethod
    def from_phase(phase: str) -> 'PodStatus':
        """Create a PodStatus from a Kubernetes pod phase string."""
        phase = phase.lower() if phase else ""

        if phase == "pending":
            return PodStatus(RunState.STARTING)
        elif phase == "running":
            return PodStatus(RunState.RUNNING)
        elif phase == "succeeded":
            return PodStatus(RunState.EXITED)
        elif phase == "failed":
            return PodStatus(RunState.DEAD)
        else:
            return PodStatus(RunState.UNKNOWN, extra={"phase": phase})


def pod_status(pod_name: str, namespace: str) -> Optional[PodStatus]:
    """Get the status of a pod. Returns None if pod not found."""
    try:
        pod = v1_api.read_namespaced_pod(name=pod_name, namespace=namespace)
        return PodStatus.from_phase(pod.status.phase)
    except ApiException as e:
        if e.status == 404:
            return None
        logger.error(f"Error checking pod status: {e}")
        return PodStatus(RunState.UNKNOWN)
    except Exception as e:
        logger.error(f"Error checking pod status: {e}")
        return PodStatus(RunState.UNKNOWN)


def is_pod_running(pod_name: str, namespace: str) -> bool:
    """Returns True if the specified pod is running."""
    status = pod_status(pod_name, namespace)
    return status is not None and status.status == RunState.RUNNING


def create_pod(pod_template: PodTemplate) -> bool:
    """Create a pod from a PodTemplate."""
    try:
        v1_api.create_namespaced_pod(
            namespace=pod_template.namespace, body=pod_template.template
        )
        logger.info(f"Created pod '{pod_template.pod_name}' in namespace '{pod_template.namespace}'.")
        return True
    except ApiException as e:
        logger.error(f"Error creating pod: {e}")
        return False
    except Exception as e:
        logger.error(f"Error creating pod: {e}")
        return False


def delete_pod(pod_name: str, namespace: str) -> bool:
    """Delete a pod by name."""
    try:
        v1_api.delete_namespaced_pod(name=pod_name, namespace=namespace)
        logger.info(f"Deleted pod '{pod_name}' in namespace '{namespace}'.")
        return True
    except ApiException as e:
        if e.status == 404:
            logger.info(f"Pod '{pod_name}' not found in namespace '{namespace}', nothing to delete.")
            return True
        logger.error(f"Error deleting pod: {e}")
        return False
    except Exception as e:
        logger.error(f"Error deleting pod: {e}")
        return False
