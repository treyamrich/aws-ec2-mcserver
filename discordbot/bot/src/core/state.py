from dataclasses import dataclass
import enum
import threading
from typing import Optional

import discord

from discordbot.bot.src.core import ec2

class RunState(enum.Enum):
    STARTING = "starting"
    RESTARTING = "restarting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    EXITED = "exited"
    PAUSED = "paused"
    DEAD = "dead"
    UNKNOWN = "unknown"
    
@dataclass
class ServerState:
    discord_guild_name: str = "MC Server"
    run_state: RunState = RunState.STOPPED
    server_status_message: Optional[discord.Interaction] = None
    connected_players: set = set()
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
        
    def set_server_run_state(self, state: RunState):
        with self._lock:
            self.server_state.run_state = state

    def get_server_status_message(self) -> Optional[discord.Interaction]:
        with self._lock:
            return self.server_state.server_status_message
        
    def set_server_status_message(self, message: discord.Interaction):
        with self._lock:
            self.server_state.server_status_message = message

    def is_server_running(self) -> bool:
        with self._lock:
            return self.server_state.run_state == RunState.RUNNING
        
    def set_ec2_instance(self, instance: 'ec2.EC2Instance'):
        with self._lock:
            self.server_state.ec2_instance = instance
    
    def get_ec2_instance(self) -> Optional['ec2.EC2Instance']:
        with self._lock:
            return self.server_state.ec2_instance

state_manager = StateManager()