import discord
import os
import subprocess
from abc import ABC, abstractmethod
from core.config import config, Deployment
from core.logger import Logger
from core.state import RunState, state_manager
import discord_embed as embed
from discordbot.bot.src.core import docker

if config.GENERAL.deployment == Deployment.AWS_EC2:
    from core import ec2

logger = Logger(os.path.basename(__file__), severity_level='debug')

def get_handler(bot) -> 'DiscordCmdHandler':
    """Factory function to get the appropriate handler."""
    if config.GENERAL.deployment == Deployment.LOCAL:
        return LocalHandler(bot)
    elif config.GENERAL.deployment == Deployment.AWS_EC2:
        return AwsEc2Handler(bot)
    logger.critical("Could not create handler. Handler not implemented for deployment.", extra={
        "deployment": config.GENERAL.deployment.value,
        "method": "get_handler"
    })

async def _exception_helper(logger, e: Exception, ctx):
    logger.error(e)
    if str(e) == "[Errno 8] nodename nor servname provided, or not known":
        await ctx.respond("Could not connect to minecraft server.")
    else:
        await ctx.respond("Error processing request.")
        
class DiscordCmdHandler(ABC):
    
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.logger = Logger('DiscordCmdHandler', severity_level='debug')

    @abstractmethod
    async def start(self, ctx: discord.ApplicationContext):
        """Start the server."""
        pass

    @abstractmethod
    async def ip(self, ctx: discord.ApplicationContext):
        """Get the server's public IP address."""
        pass
            
    @abstractmethod
    def update_server_state(self):
        """Update the server state."""
        pass        
    
    async def ping(self, ctx):
        """Get the server's ping."""
        await ctx.respond(f"Pong! Latency is {int(self.bot.latency * 1000)} ms")
        
    async def _poll_and_send_server_start(self, ctx: discord.ApplicationContext):
        state_manager.set_server_run_state(RunState.STARTING)
        bot_response = await ctx.respond(embed=embed.server_status())
        original_msg = await bot_response.original_message()
        state_manager.set_server_status_message(original_msg)
            
    
    
class AwsEc2Handler(DiscordCmdHandler):
    
    async def start(self, ctx: discord.ApplicationContext):
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
        state_manager.reset()
        state_manager.set_discord_guild_name(ctx.guild.name)
        state_manager.set_ec2_instance(instance)
        await self._poll_and_send_server_start(ctx)

    async def ip(self, ctx: discord.ApplicationContext):
        """Get the server's public IP address."""
        try:
            instance = ec2.getServerInstance()  
            instance_ip = instance.publicIp if instance else "Unknown"
            await ctx.respond(f"The server's public IP address is: {instance_ip}")
        except Exception as e:
            await _exception_helper(e, ctx)
            
    def update_server_state(self):
        """Update the server state."""
        instance = ec2.getServerInstance()
        if instance:
            state_manager.set_server_run_state(RunState.RUNNING)
            state_manager.set_connected_players(instance.getConnectedPlayers())
        else:
            state_manager.set_server_run_state(RunState.STOPPED)
            state_manager.set_connected_players(set())
            

class LocalHandler(DiscordCmdHandler):

    async def start(self, ctx: discord.ApplicationContext):
        """Start the Minecraft server locally."""
        if docker.is_container_running(config.GENERAL.docker_compose_slug):
            self.logger.info(f"Server is already running locally with slug {config.GENERAL.docker_compose_slug}", extra={'method': 'start'})
            await ctx.respond(f"The server is already running :yawning_face:")
            return
        
        state_manager.reset()
        
        try:
            # Ensure no existing containers are running before starting a new one
            subprocess.run(
                ["docker", "compose", "-p", config.GENERAL.docker_compose_slug, "-f", "/data/compose.yaml", "down"],
                check=True,
                capture_output=True,
                text=True
            )
            subprocess.run(
                ["docker", "compose", "-p", config.GENERAL.docker_compose_slug, "-f", "/data/compose.yaml", "up", "-d"],
                check=True,
                capture_output=True,
                text=True
            )
            self.logger.info("Local server started using Docker Compose.")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to start local server: {e.stderr}")
            await ctx.respond("Failed to start the server :cry:")
            return
        
        state_manager.set_discord_guild_name(ctx.guild.name)
        await self._poll_and_send_server_start(ctx)
    
    async def ip(self, ctx: discord.ApplicationContext):
        """Get the server's public IP address locally."""
        await ctx.respond(f"Server is hosted locally. IP Address not available.")
        
    def update_server_state(self):
        """Update the server state for local deployment."""
        container_status = docker.container_status(config.GENERAL.docker_compose_slug)
        state_manager.set_server_run_state(container_status.status)