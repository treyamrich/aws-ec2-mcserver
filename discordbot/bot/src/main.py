import discord
import os
from core.config import config
from core.logger import Logger
from handler import get_handler

bot = discord.Bot(debug_guilds=config.DISCORD.debug_guild_ids)
handler = get_handler(bot)
logger = Logger(os.path.basename(__file__), severity_level='debug')

@bot.command(description="Starts the Minecraft server")
async def start(ctx):
    await ctx.respond(f"Processing request :robot:")
    await handler.start(ctx)

@bot.command(description="Lists number of players and ping.")
async def status(ctx):
    await handler.status(ctx)

@bot.command(description="Get the server's public IP address.")
async def ip(ctx):
    await handler.ip(ctx)

@bot.command(description="Lists the connected players")
async def online_players(ctx):
    await handler.online_players(ctx)
    
@bot.command(description="Sends the bot's latency.")
async def ping(ctx):
    await handler.ping(ctx)


@bot.event
async def on_ready():
    logger.info(f"{bot.user.name} has connected to Discord!")

try:
    bot.run(config.DISCORD.api_token)
except Exception as e:
    logger.critical(e)
