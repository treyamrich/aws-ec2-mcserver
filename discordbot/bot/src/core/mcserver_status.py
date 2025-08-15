
import socket
from typing import Any, Callable, Optional, Set, Union
from mcstatus import JavaServer, BedrockServer

from core.config import config
import os
from core.logger import Logger

logger = Logger(os.path.basename(__file__), severity_level='debug')

class MinecraftServer:

    def __init__(self, address: str, port: int, is_bedrock: bool = False):
        cls = BedrockServer if is_bedrock else JavaServer
        self._server: Union[BedrockServer, JavaServer] = cls(address, port)

    def is_server_running(self) -> bool:
        """Check if the server is running."""
        return self.ping() is not None

    def ping(self) -> Optional[float]:
        return self._rescue("ping", lambda: int(self._server.ping()), None)

    def list_players(self) -> Optional[Set[str]]:
        def _get_player_names() -> Set[str]:
            players = self._server.query().players.names
            return set(players)
        return self._rescue("list_players", _get_player_names, None)
    
    def _rescue(self, func_name: str, func: Callable, default_return: Any):
        """Helper to rescue from exceptions and return a default value."""
        try:
            return func()
        except (ConnectionRefusedError, socket.timeout) as e:
            logger.debug(f"Could not connect to Minecraft server: {e}", extra={"method": func_name})
            return default_return
        except Exception as e:
            logger.error(f"Error in MinecraftServer.py method '{func_name}': {e}")
            return default_return
    
address, port = config.MINECRAFT.server_status_host, config.MINECRAFT.server_port_java
mcserver = MinecraftServer(address, port, is_bedrock=False)