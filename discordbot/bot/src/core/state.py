from dataclasses import dataclass, field
import enum
import json
import threading
from typing import Optional, TYPE_CHECKING

from core.config import config
from core.logger import Logger
from mcserver_status import mcserver

if TYPE_CHECKING:
    from core import ec2
    
logger = Logger('StateManager', severity_level='debug')

class RunState(enum.Enum):
    STARTING = "starting"
    RESTARTING = "restarting"
    RUNNING = "running"
    STOPPED = "stopped"
    EXITED = "exited"
    PAUSED = "paused"
    DEAD = "dead"
    UNKNOWN = "unknown"
    
@dataclass
class ServerState:
    discord_guild_name: str = "MC Server"
    run_state: RunState = RunState.STOPPED
    server_status_msg_id: Optional[int] = None
    server_status_msg_channel_id: Optional[int] = None
    connected_players: set = field(default_factory=set)
    ec2_instance: Optional['ec2.EC2Instance'] = None
    
class StateManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StateManager, cls).__new__(cls)
            cls._instance.server_state = ServerState()
        return cls._instance
    
    def reset(self):
        """Reset the state to a fresh instance. Usually called when the server is started again."""
        with self._lock:
            self.server_state = ServerState()

    def get_discord_guild_name(self) -> str:
        with self._lock:
            return self.server_state.discord_guild_name
        
    def set_discord_guild_name(self, guild_name: str):
        with self._lock:
            self.server_state.discord_guild_name = guild_name

    def get_connected_players(self) -> set:
        with self._lock:
            return self.server_state.connected_players
    
    def set_connected_players(self, players: set):
        with self._lock:
            self.server_state.connected_players = players

    def get_server_run_state(self) -> RunState:
        with self._lock:
            return self.server_state.run_state
        
    def set_server_state_running(self):
        """Set the server state to running."""
        with self._lock:
            self.server_state.run_state = RunState.RUNNING
            
    def update_server_run_state(self):
        is_remote_running = mcserver.is_server_running()
        with self._lock:
            # This is a mini FSM
            curr_state = self.server_state.run_state
            if curr_state == RunState.STARTING and is_remote_running:
                self.server_state.run_state = RunState.RUNNING
            elif curr_state == RunState.RUNNING and not is_remote_running:
                self.server_state.run_state = RunState.STOPPED
            elif curr_state == RunState.STOPPED and is_remote_running:
                self.server_state.run_state = RunState.RUNNING

    def get_server_status_channel_and_msg_id(self) -> Optional[tuple[int, int]]:
        with self._lock:
            return (self.server_state.server_status_msg_channel_id, self.server_state.server_status_msg_id)

    def set_server_status_channel_and_msg_id(self, channel_id: int, msg_id: int):
        with self._lock:
            self.server_state.server_status_msg_channel_id = channel_id
            self.server_state.server_status_msg_id = msg_id

    def is_server_running(self) -> bool:
        with self._lock:
            return self.server_state.run_state == RunState.RUNNING
        
    def set_ec2_instance(self, instance: 'ec2.EC2Instance'):
        with self._lock:
            self.server_state.ec2_instance = instance
    
    def get_ec2_instance(self) -> Optional['ec2.EC2Instance']:
        with self._lock:
            return self.server_state.ec2_instance
        
    def save_to_file(self):
        try:
            data = {
                "server_status_msg_channel_id": self.server_state.server_status_msg_channel_id,
                "server_status_msg_id": self.server_state.server_status_msg_id
            }
            with open(config.DISCORD.server_state_filename, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving server state to file: {e}")

    def load_from_file(self):
        """Load the server state from a file. This should only be called if the server is running!"""
        try:
            with open(config.DISCORD.server_state_filename, "r") as f:
                data = json.load(f)
            channel_id = int(data.get("server_status_msg_channel_id", 0))
            msg_id = int(data.get("server_status_msg_id", 0))
        except Exception as e:
            logger.error(f"Error loading server state from file: {e}")
            return

        with self._lock:
            if "server_status_msg_channel_id" in data:
                self.server_state.server_status_msg_channel_id = channel_id
            if "server_status_msg_id" in data:
                self.server_state.server_status_msg_id = msg_id
            self.server_state.run_state = RunState.RUNNING

state_manager = StateManager()