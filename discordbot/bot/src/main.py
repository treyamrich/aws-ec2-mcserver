import discord
import os
from discord.ext import tasks, commands
from discord.commands import SlashCommandGroup

from core.config import config
from core.logger import Logger
from core.state import state_manager
from discordbot.bot.src import discord_embed
from handler import get_handler

bot = discord.Bot(debug_guilds=config.DISCORD.debug_guild_ids)
logger = Logger(os.path.basename(__file__), severity_level='debug')

class MainCog(commands.Cog):
    
    server = SlashCommandGroup("server", "Commands related to the Minecraft server")
    
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.handler = get_handler(bot)
        
        self.update_server_status_loop.start()

    @server.command(description="Starts the Minecraft server")
    async def start(self, ctx: discord.ApplicationContext):
        await ctx.respond(f"Processing request :robot:")
        await self.handler.start(ctx)
        
    @tasks.loop(seconds=15)
    async def update_server_status_loop(self):
        log_vars = {"method": "update_server_status_loop"}

        try:
            current_connected_players = state_manager.get_connected_players()
            state_manager.update_server_run_state()
                
            if not state_manager.is_server_running():
                logger.info("Server not running, waiting for it to start.", extra=log_vars)
                return

            # Update the connected players only if there is a change
            if current_connected_players == state_manager.get_connected_players():
                return
            
            # If the status message even exists from starting the server
            channel_id, msg_id = state_manager.get_server_status_channel_and_msg_id()
            if msg_id and channel_id:
                channel = self.bot.get_channel(channel_id)
                embed = discord_embed.server_status()
                message = await channel.fetch_message(msg_id)
                await message.edit(embed=embed)
                logger.debug("Updated server status embed with new connected players.", extra=log_vars)
        except Exception as e:
            logger.error(f"Error updating server state: {e}", extra=log_vars)

    @bot.command(description="Lists number of players and ping.")
    async def status(self, ctx: discord.ApplicationContext):
        await self.handler.status(ctx)

    @server.command(description="Get the server's public IP address.")
    async def ip(self, ctx: discord.ApplicationContext):
        await self.handler.ip(ctx)

    @server.command(description="Sends the bot's latency.")
    async def ping(self, ctx: discord.ApplicationContext):
        await self.handler.ping(ctx)

    @bot.event
    async def on_ready():
        logger.info(f"{bot.user.name} has connected to Discord!")
        
        # If server was running before bot started
        state_manager.update_server_run_state()
        if state_manager.is_server_running():
            state_manager.load_from_file()

try:
    bot.add_cog(MainCog(bot))
    bot.run(config.DISCORD.api_token)
except Exception as e:
    logger.critical(e)
