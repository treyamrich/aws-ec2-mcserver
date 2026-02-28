
import os
from typing import Optional

from kubernetes import client, config as kube_config
from kubernetes.client.rest import ApiException

from core.config import KubernetesConfig
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


def create_mc_server_pod(k8s_config: KubernetesConfig) -> bool:
    """Create a Minecraft server pod using the provided KubernetesConfig."""
    pod = client.V1Pod(
        metadata=client.V1ObjectMeta(
            name=k8s_config.mc_pod_name,
            namespace=k8s_config.namespace,
            labels={"app": "mc-server"},
            annotations={"backup.velero.io/backup-volumes": "world-data"},
        ),
        spec=client.V1PodSpec(
            restart_policy="Never",
            containers=[
                client.V1Container(
                    name="mc-server",
                    image=k8s_config.mc_image,
                    ports=[
                        client.V1ContainerPort(container_port=25565, protocol="TCP"),
                        client.V1ContainerPort(container_port=25565, protocol="UDP"),
                    ],
                    env_from=[
                        client.V1EnvFromSource(
                            config_map_ref=client.V1ConfigMapEnvSource(
                                name=k8s_config.mc_configmap_name
                            )
                        )
                    ],
                    volume_mounts=[
                        client.V1VolumeMount(
                            name="world-data",
                            mount_path="/data",
                        )
                    ],
                )
            ],
            volumes=[
                client.V1Volume(
                    name="world-data",
                    persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                        claim_name=k8s_config.mc_pvc_name
                    ),
                )
            ],
        ),
    )

    try:
        v1_api.create_namespaced_pod(namespace=k8s_config.namespace, body=pod)
        logger.info(f"Created MC server pod '{k8s_config.mc_pod_name}' in namespace '{k8s_config.namespace}'.")
        return True
    except ApiException as e:
        logger.error(f"Error creating MC server pod: {e}")
        return False
    except Exception as e:
        logger.error(f"Error creating MC server pod: {e}")
        return False


def delete_mc_server_pod(pod_name: str, namespace: str) -> bool:
    """Delete the Minecraft server pod."""
    try:
        v1_api.delete_namespaced_pod(name=pod_name, namespace=namespace)
        logger.info(f"Deleted MC server pod '{pod_name}' in namespace '{namespace}'.")
        return True
    except ApiException as e:
        if e.status == 404:
            logger.info(f"Pod '{pod_name}' not found in namespace '{namespace}', nothing to delete.")
            return True
        logger.error(f"Error deleting MC server pod: {e}")
        return False
    except Exception as e:
        logger.error(f"Error deleting MC server pod: {e}")
        return False
