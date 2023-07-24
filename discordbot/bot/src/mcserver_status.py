from mcstatus import JavaServer
from mcstatus import BedrockServer

from util import config
import os
from util.logger import Logger

logger = Logger(os.path.basename(__file__), config.LOGGER_PATH, severity_level='debug')

class MinecraftServer:
    
    def __init__(self, server_type, address, port):
        self.address, self.port = address, port
        self.server_type = server_type
        self.server = server_type.lookup(f"{self.address}:{self.port}")
    
    def ping(self):
        return self.server.ping()
        
    def list_players(self):
        func_name = "list_players"
        if self.server_type == BedrockServer:
            logger.warning('Cannot query on bedrock')
            return
        return logger.log_with_info(self.server.query, func_name)
        
    def list_status(self):
        func_name = "list_status"
        return logger.log_with_info(self.server.status, func_name)
        
class MinecraftServerBuilder:
    
    def __init__(self, address, port):
        self.address = address
        self.port = port
        
    def _build_server(self, server_type):
        return MinecraftServer(server_type, self.address, self.port)
            
    def build_java_server(self):
        return self._build_server(JavaServer)
    
    def build_bedrock_server(self):
        return self._build_server(BedrockServer)
    
mcserver = None
try:
    address, port = config.SERVER_ADDRESS, config.SERVER_PORT_JAVA
    mcserver = MinecraftServerBuilder(address, port) \
		.build_java_server()
    latency = int(mcserver.ping())
    logger.info(f"Connected to server at {address}:{port}. Ping {latency} ms.")
except Exception as e:
    logger.error(e)