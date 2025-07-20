import discord
from core.config import config
from core.logger import Logger
from mcserver_status import mcserver

logger = Logger('DiscordEmbed', severity_level='debug')

def server_status(ip_address = 'Unknown') -> discord.Embed:
    """Common method to get the discord 'Embed' for the server status."""
    status = mcserver.list_status()
        
    num_players, latency = status.players.online, int(status.latency)
    status_str = (
        f"There are {num_players} players online. Response in {latency} ms."
    )
    logger.debug(status_str, extra={'method': 'server_status'})

    embed = discord.Embed(
        title=config.MINECRAFT.server_address, description="Server status", color=0x18CF9B
    )
    
    embed.add_field(name="Number of players", value=num_players)
    embed.add_field(name="Ping", value=f"{latency} ms")
    embed.add_field(
        name="Server Domain", value=f"**{config.MINECRAFT.server_address}**", inline=False
    )
    embed.add_field(
        name="Server IP Address", value=f"**{ip_address}**", inline=False
    )
    return embed

def server_start(guild_name):
    desc = ":desktop: Server is booting up. Pls wait __5 min__ :pray:"
    embed = discord.Embed(title=guild_name, description=desc, color=0x18CF9B)
    embed.add_field(
        name="Server Address", value=f"**{config.MINECRAFT.server_address}**", inline=False
    )
    embed.add_field(
        name="Server Notice",
        value="- The server will be automatically turned off if there are __0 players connections for 30 minutes__.",
        inline=False,
    )
    if config.MINECRAFT.server_map_port:
        embed.add_field(
            name="Server Map",
            value=f"http://{config.MINECRAFT.server_address}:{config.MINECRAFT.server_map_port}/",
        )
    # embed.set_image(url="https://play-lh.googleusercontent.com/VSwHQjcAttxsLE47RuS4PqpC4LT7lCoSjE7Hx5AW_yCxtDvcnsHHvm5CTuL5BPN-uRTP=w240-h480-rw")
    if config.MINECRAFT.thumbnail_url:
        embed.set_thumbnail(url=config.MINECRAFT.thumbnail_url)
    return embed
    