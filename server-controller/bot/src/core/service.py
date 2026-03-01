"""
Service layer — transport-agnostic business logic for server management.

Both the Discord handler and the HTTP test server delegate to these services.
"""

import enum
import os
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from core.config import config, Deployment
from core.logger import Logger
from core.state import state_manager, RunState

logger = Logger(os.path.basename(__file__))


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

class StartOutcome(enum.Enum):
    STARTED = "started"
    ALREADY_RUNNING = "already_running"
    ALREADY_STARTING = "already_starting"
    FAILED = "failed"
    ERROR = "error"


@dataclass
class StartResult:
    outcome: StartOutcome
    message: Optional[str] = None


@dataclass
class StopResult:
    success: bool
    message: Optional[str] = None


@dataclass
class StatusResult:
    run_state: Optional[RunState]
    message: str


@dataclass
class IpResult:
    ip: Optional[str]
    message: str


# ---------------------------------------------------------------------------
# Service ABC
# ---------------------------------------------------------------------------

class ServerService(ABC):

    @abstractmethod
    def start(self) -> StartResult:
        """Start the server. Returns a StartResult."""

    @abstractmethod
    def stop(self) -> StopResult:
        """Stop the server. Returns a StopResult."""

    @abstractmethod
    def status(self) -> StatusResult:
        """Query infrastructure for the current server status."""

    @abstractmethod
    def ip(self) -> IpResult:
        """Get the server's IP address."""

    def _do_start_finalize(self):
        """Common finalization after a successful start"""
        state_manager.set_server_state_running()


# ---------------------------------------------------------------------------
# Kubernetes
# ---------------------------------------------------------------------------

class KubernetesService(ServerService):

    def __init__(self):
        import k8s
        self._k8s = k8s
        self.pod_template = k8s.PodTemplate.from_file(config.KUBERNETES.pod_template_path)

    def start(self) -> StartResult:
        pt = self.pod_template
        try:
            status = self._k8s.pod_status(pt.pod_name, pt.namespace)

            if status is None:
                state_manager.reset()
                if not self._k8s.create_pod(pt):
                    return StartResult(StartOutcome.FAILED, "Failed to create pod.")
                self._do_start_finalize()
                return StartResult(StartOutcome.STARTED)

            if status.status == RunState.STARTING:
                return StartResult(StartOutcome.ALREADY_STARTING, "Server is already starting, please wait.")

            if status.status == RunState.RUNNING:
                return StartResult(StartOutcome.ALREADY_RUNNING, "The server is already running.")

            if status.status in (RunState.EXITED, RunState.DEAD, RunState.UNKNOWN):
                self._k8s.delete_pod(pt.pod_name, pt.namespace)
                state_manager.reset()
                if not self._k8s.create_pod(pt):
                    return StartResult(StartOutcome.FAILED, "Failed to create pod after cleanup.")
                self._do_start_finalize()
                return StartResult(StartOutcome.STARTED)

        except Exception as e:
            logger.error(e)
            return StartResult(StartOutcome.ERROR, str(e))

        return StartResult(StartOutcome.ERROR, "Unexpected pod state.")

    def stop(self) -> StopResult:
        pt = self.pod_template
        ok = self._k8s.delete_pod(pt.pod_name, pt.namespace)
        return StopResult(success=ok, message="Deleted" if ok else "Failed to delete pod.")

    def status(self) -> StatusResult:
        pt = self.pod_template
        ps = self._k8s.pod_status(pt.pod_name, pt.namespace)
        if ps is None:
            return StatusResult(run_state=None, message="not_found")
        return StatusResult(run_state=ps.status, message=ps.status.value)

    def ip(self) -> IpResult:
        return IpResult(ip=None, message="Server is hosted on Kubernetes. Use the server address to connect.")


# ---------------------------------------------------------------------------
# Local (Docker Compose)
# ---------------------------------------------------------------------------

class LocalService(ServerService):

    def __init__(self):
        from core import docker_util
        self._docker_util = docker_util

    def start(self) -> StartResult:
        if self._docker_util.is_container_running(config.GENERAL.mc_server_container_name):
            return StartResult(StartOutcome.ALREADY_RUNNING, "The server is already running.")

        state_manager.reset()

        try:
            subprocess.run(
                ["docker", "compose", "-p", config.GENERAL.mc_server_container_name, "-f", "/data/compose.yaml", "down"],
                check=True, capture_output=True, text=True,
            )
            subprocess.run(
                ["docker", "compose", "-p", config.GENERAL.mc_server_container_name, "-f", "/data/compose.yaml", "up", "-d"],
                check=True, capture_output=True, text=True,
            )
            logger.info("Local server started using Docker Compose.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start local server: {e.stderr}")
            return StartResult(StartOutcome.FAILED, "Failed to start the server.")

        self._do_start_finalize()
        return StartResult(StartOutcome.STARTED)

    def stop(self) -> StopResult:
        try:
            subprocess.run(
                ["docker", "compose", "-p", config.GENERAL.mc_server_container_name, "-f", "/data/compose.yaml", "down"],
                check=True, capture_output=True, text=True,
            )
            return StopResult(success=True, message="Server stopped.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to stop local server: {e.stderr}")
            return StopResult(success=False, message="Failed to stop the server.")

    def status(self) -> StatusResult:
        cs = self._docker_util.container_status(config.GENERAL.mc_server_container_name)
        return StatusResult(run_state=cs.status, message=cs.status.value)

    def ip(self) -> IpResult:
        return IpResult(ip=None, message="Server is hosted locally. IP Address not available.")


# ---------------------------------------------------------------------------
# AWS EC2
# ---------------------------------------------------------------------------

class AwsEc2Service(ServerService):

    def __init__(self):
        from core import ec2
        self._ec2 = ec2

    def start(self) -> StartResult:
        instance = self._ec2.startServer()

        if len(instance.errors) > 0:
            return StartResult(StartOutcome.FAILED, "Server failure.")

        if not instance.isNew:
            return StartResult(StartOutcome.ALREADY_RUNNING, "The server is already running.")

        state_manager.reset()
        state_manager.set_ec2_instance(instance)
        self._do_start_finalize()
        return StartResult(StartOutcome.STARTED)

    def stop(self) -> StopResult:
        return StopResult(success=False, message="EC2 stop not implemented.")

    def status(self) -> StatusResult:
        run_state = state_manager.get_server_run_state()
        return StatusResult(run_state=run_state, message=run_state.value)

    def ip(self) -> IpResult:
        try:
            instance = self._ec2.getServerInstance()
            ip = instance.publicIp if instance else None
            msg = f"The server's public IP address is: {ip}" if ip else "Unknown"
            return IpResult(ip=ip, message=msg)
        except Exception as e:
            logger.error(e)
            return IpResult(ip=None, message="Error retrieving IP address.")


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_service() -> ServerService:
    if config.GENERAL.deployment == Deployment.LOCAL:
        return LocalService()
    elif config.GENERAL.deployment == Deployment.AWS_EC2:
        return AwsEc2Service()
    elif config.GENERAL.deployment == Deployment.KUBERNETES:
        return KubernetesService()
    raise ValueError(f"No service implemented for deployment: {config.GENERAL.deployment.value}")
