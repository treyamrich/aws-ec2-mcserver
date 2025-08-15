
import os
import docker
from typing import Optional

from .logger import Logger
from .state import RunState

logger = Logger(os.path.basename(__file__), severity_level='debug')
client = docker.from_env()

class ContainerStatus:
    def __init__(self, status: RunState, extra: Optional[dict] = None):
        self.status = status
        self.extra = extra
        
    @staticmethod
    def from_string(status_str: str) -> 'ContainerStatus':
        """Create a ContainerStatus from a string representation."""
        status_str = status_str.lower()

        if status_str.startswith("running"):
            return ContainerStatus(RunState.RUNNING)

        if status_str.startswith("exited"):
            return ContainerStatus(RunState.EXITED)

        if "created" in status_str:
            return ContainerStatus(RunState.STARTING)

        if "restarting" in status_str:
            return ContainerStatus(RunState.RESTARTING)

        if "paused" in status_str:
            return ContainerStatus(RunState.PAUSED)

        if "dead" in status_str:
            return ContainerStatus(RunState.DEAD)

        return ContainerStatus(RunState.UNKNOWN, extra={"status_str": status_str})

def container_status(container_name: str) -> ContainerStatus:
    try:
        container = client.containers.get(container_name)
        return ContainerStatus.from_string(container.status)
    except Exception as e:
        # Handle errors as needed
        logger.error(f"Error checking container status: {e}")
        return ContainerStatus(RunState.UNKNOWN)

def is_container_running(container_name: str) -> bool:
    """Returns True if the specified container is running."""
    return container_status(container_name).status == RunState.RUNNING
