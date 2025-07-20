import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class Deployment(Enum):
    LOCAL = "local"
    AWS_EC2 = "aws_ec2"

@dataclass
class DiscordConfig:
    api_token: str
    debug_guild_ids: list

@dataclass
class MCServerConfig:
    server_address: str
    server_port_java: int
    server_port_bedrock: int
    server_map_port: Optional[int] = None
    thumbnail_url: str
   
@dataclass 
class AWSConfig:
    server_tag: str
    region: str
    launch_template_name: str
    
@dataclass
class GeneralConfig:
    deployment: Deployment
    docker_compose_file_path: str
    duck_dns_token: str
    duck_dns_domain: str

class Config:
    
    def __init__(self):
        self._general = GeneralConfig(
            deployment=Deployment(os.getenv('DEPLOYMENT', 'local')),
            docker_compose_file_path=os.getenv('DOCKER_COMPOSE_FILE_PATH', '.'), # Only applicable for local deployment
            duck_dns_token=os.getenv('DUCK_DNS_TOKEN'),
            duck_dns_domain=os.getenv('DUCK_DNS_DOMAIN')
        )

        self._discord = DiscordConfig(
            api_token=os.getenv('DISCORD_API_TOKEN'),
            debug_guild_ids=[x.strip() for x in os.getenv('DISCORD_DEBUG_GUILD_IDS', '').split(',') if x.strip()],
        )

        self._mcserver = MCServerConfig(
            server_address=os.getenv('SERVER_ADDRESS'),
            server_port_java=int(os.getenv('SERVER_PORT_JAVA', 25565)),
            server_port_bedrock=int(os.getenv('SERVER_PORT_BEDROCK', 19132)),
            server_map_port=int(os.getenv('SERVER_MAP_PORT')) if os.getenv('SERVER_MAP_PORT') is not None else None,
            thumbnail_url=os.getenv('SERVER_THUMBNAIL_URL')
        )

        self._aws = AWSConfig(
            server_tag=os.getenv('AWS_SERVER_TAG'),
            region=os.getenv('AWS_REGION'),
            launch_template_name=os.getenv('AWS_LAUNCH_TEMPLATE_NAME')
        )
        
    @property
    def GENERAL(self):
        return self._general
    
    @property
    def DISCORD(self):
        return self._discord
    
    @property
    def MINECRAFT(self):
        return self._mcserver

    @property
    def AWS(self):
        return self._aws

config = Config()