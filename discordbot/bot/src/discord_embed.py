import os
import discord
from core.config import Deployment, config
from core.logger import Logger
from core.state import state_manager
from core import ec2
from core.mcserver_status import mcserver

logger = Logger(os.path.basename(__file__))

def server_status() -> discord.Embed:
    guild_name = state_manager.get_discord_guild_name()
    desc = ":desktop: The server will be automatically turned off if there are __0 players connections for 30 minutes__."
    embed = discord.Embed(title=guild_name, description=desc, color=0x18CF9B)
    embed.add_field(
        name="Server Address", value=config.MINECRAFT.server_address, inline=False
    )
    
    if config.MINECRAFT.server_map_port:
        embed.add_field(
            name="Server Map",
            value=f"http://{config.MINECRAFT.server_address}:{config.MINECRAFT.server_map_port}/",
        )

    if config.MINECRAFT.thumbnail_url:
        embed.set_thumbnail(url=config.MINECRAFT.thumbnail_url)
    
    _set_server_status(embed)
    _set_server_deployment_footer(embed)
    return embed
    
def _set_server_status(embed: discord.Embed):
    status = state_manager.get_server_run_state()
    embed.add_field(
        name="Server Status",
        value=f"{status.value.capitalize()}",
        inline=False
    )

    connected_players = mcserver.list_players() or set()
    connected_players_msg = [f"- {player}" for player in connected_players]
    embed.add_field(name="Number of players", value=len(connected_players))
    embed.add_field(
        name="Connected Players",
        value="\n".join(connected_players_msg) if connected_players else "None",
        inline=False,
    )

def _set_server_deployment_footer(embed: discord.Embed):
    """Add the server deployment information to the embed."""
    if config.GENERAL.deployment == Deployment.LOCAL:
        embed.set_footer(
            text=f"Server hosted locally"
        )
    elif config.GENERAL.deployment == Deployment.AWS_EC2:
        instance = ec2.getServerInstance()
        instance_type = instance.instanceType if instance else "Unknown"
        ip = instance.public_ip if instance else "Unknown"
        embed.set_footer(
            text=f"Server hosted on AWS Spot EC2. Instance Type: {instance_type}. IP: {ip}."
        )
    else:
        embed.set_footer(
            text=f"Server hosted on {config.GENERAL.deployment.value}"
        )