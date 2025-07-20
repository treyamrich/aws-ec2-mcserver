import discord
import subprocess
from abc import ABC, abstractmethod
from core.config import config, Deployment
from core.logger import Logger
from core import ec2
from mcserver_status import mcserver
import discord_embed as embed

def get_handler(bot) -> 'DiscordCmdHandler':
    """Factory function to get the appropriate handler."""
    if config.GENERAL.deployment == Deployment.LOCAL:
        pass
    elif config.GENERAL.deployment == Deployment.AWS_EC2:
        pass
    
async def _exception_helper(logger, e: Exception, ctx):
    logger.error(e)
    if str(e) == "[Errno 8] nodename nor servname provided, or not known":
        await ctx.respond("Could not connect to minecraft server.")
    else:
        await ctx.respond("Error processing request.")
        
class DiscordCmdHandler(ABC):
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = Logger('DiscordCmdHandler', severity_level='debug')

    @abstractmethod
    async def start(self, ctx):
        """Start the server."""
        pass
    
    @abstractmethod
    async def status(self, ctx):
        """Get the server status."""
        pass

    @abstractmethod
    async def ip(self, ctx):
        """Get the server's public IP address."""
        pass
    
    async def online_players(self, ctx):
        """Get the list of online players."""
        try:
            query = mcserver.list_players()
            players_str = ", ".join(query.players.names)
            player_list = query.players.names
            players_str = f"The server has the following players online: {players_str}"
            self.logger.debug(players_str)

            embed = discord.Embed(
                title=config.MINECRAFT.server_address, description="Server status", color=0x18CF9B
            )
            embed.add_field(name="Number of players", value=len(player_list))
            embed.add_field(name="Online Players", value="\n".join(player_list))
            await ctx.respond(embed=embed)
        except Exception as e:
            await _exception_helper(e, ctx)
            
    async def ping(self, ctx):
        """Get the server's ping."""
        await ctx.respond(f"Pong! Latency is {int(self.bot.latency * 1000)} ms")
    
    
class AwsEc2Handler(DiscordCmdHandler):
    
    async def start(self, ctx):
        """Start the Minecraft server on AWS EC2."""
        
        instance = ec2.startServer()

        if len(instance.errors) > 0:
            await ctx.respond(
                "**Error:** Server failure. :cry: Please contact your administrator."
            )
            return

        # If server already running
        if not instance.isNew:
            await ctx.respond(f"The server is already running :yawning_face:")
            self.logger.debug(f"Server is already running at {config.MINECRAFT.server_address}")
            return

        self.logger.info("Server boot initiated")

        embed_res = embed.server_start(ctx.guild.name)
        embed_res.set_footer(
            text=f"Server hosted on AWS Spot EC2. Instance Type: {instance.instanceType}"
        )
        await ctx.respond(embed=embed_res)

    async def status(self, ctx):
        """Get the Minecraft server status on AWS EC2."""
        try:
            instance = ec2.getServerInstance()
            instance_ip = instance.publicIp if instance else "Unknown"
            embed_res = embed.server_status(instance_ip)
            await ctx.respond(embed=embed_res)
        except Exception as e:
            await _exception_helper(e, ctx)
    
    async def ip(self, ctx):
        """Get the server's public IP address."""
        try:
            instance = ec2.getServerInstance()  
            instance_ip = instance.publicIp if instance else "Unknown"
            await ctx.respond(f"The server's public IP address is: {instance_ip}")
        except Exception as e:
            await _exception_helper(e, ctx)
            

class LocalHandler(DiscordCmdHandler):
    
    async def start(self, ctx):
        """Start the Minecraft server locally."""
        try:
            subprocess.run(
                ["docker", "compose", "-f", config.GENERAL.docker_compose_file_path, "up", "-d"],
                check=True,
                capture_output=True,
                text=True
            )
            self.logger.info("Local server started using Docker Compose.")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to start local server: {e.stderr}")
            await ctx.respond("Failed to start the server :cry:")
            return
        
        embed_res = embed.server_start(ctx.guild.name)
        embed_res.set_footer(
            text=f"Server hosted locally via TailScale"
        )
        await ctx.respond(embed=embed_res)
    
    async def status(self, ctx):
        """Get the Minecraft server status locally."""
        try:
            embed_res = embed.server_status()
            await ctx.respond(embed=embed_res)
        except Exception as e:
            await _exception_helper(e, ctx)
    
    async def ip(self, ctx):
        """Get the server's public IP address locally."""
        await ctx.respond(f"Server is hosted locally. IP Address not available.")