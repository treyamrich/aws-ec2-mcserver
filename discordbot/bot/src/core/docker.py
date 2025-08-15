
import os
import subprocess
from typing import Optional

from discordbot.bot.src.core.logger import Logger
from discordbot.bot.src.core.state import RunState

logger = Logger(os.path.basename(__file__), severity_level='debug')
    
class ContainerStatus:
    def __init__(self, status: RunState, extra: Optional[dict] = None):
        self.status = status
        self.extra = extra
        
    @staticmethod
    def from_string(status_str: str) -> 'ContainerStatus':
        """Create a ContainerStatus from a string representation."""
        status_str = status_str.lower()

        if status_str.startswith("up"):
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
        result = subprocess.run(
            [
                "docker", "ps",
                "--filter", f"label=com.docker.compose.project={container_name}",
                "--format", "{{.Names}}|{{.Status}}"
            ],
            capture_output=True,
            text=True,
            check=True
        )
        if not result.stdout.strip():
            logger.warning(f"No containers found for {container_name}.")
            return ContainerStatus(RunState.UNKNOWN)
        
        _, status_str = result.stdout.strip().split("|")
        return ContainerStatus.from_string(status_str)
    except Exception as e:
        # Handle errors as needed
        print(f"Error checking compose stack: {e}")
        return ContainerStatus(RunState.UNKNOWN)

def is_container_running(self, container_name: str) -> bool:
    """Returns True if the specified container is running."""
    return self.container_status(container_name).status == RunState.RUNNING