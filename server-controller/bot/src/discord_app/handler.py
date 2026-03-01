import discord
import os

from discord_app import embed
from core.logger import Logger
from core.state import state_manager
from core.service import get_service, StartOutcome

logger = Logger(os.path.basename(__file__))


class DiscordHandler:

    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.service = get_service()

    async def start(self, ctx: discord.ApplicationContext):
        """Start the server and respond via Discord."""
        result = self.service.start()

        if result.outcome == StartOutcome.STARTED:
            await self._finalize_discord_start(ctx)

        elif result.outcome == StartOutcome.ALREADY_RUNNING:
            await ctx.respond("The server is already running :yawning_face:")

        elif result.outcome == StartOutcome.ALREADY_STARTING:
            await ctx.respond("Server is already starting, please wait.")

        elif result.outcome == StartOutcome.FAILED:
            await ctx.respond("Failed to start the server :cry:")

        elif result.outcome == StartOutcome.ERROR:
            if result.message and result.message == "[Errno 8] nodename nor servname provided, or not known":
                await ctx.respond("Could not connect to minecraft server.")
            else:
                await ctx.respond("Error processing request.")

    async def status(self, ctx: discord.ApplicationContext):
        """Get the server's status."""
        await ctx.respond(embed=embed.server_status())

    async def ip(self, ctx: discord.ApplicationContext):
        """Get the server's IP address."""
        ip_result = self.service.ip()
        await ctx.respond(ip_result.message)

    async def ping(self, ctx: discord.ApplicationContext):
        """Get the bot's latency."""
        await ctx.respond(f"Pong! Latency is {int(self.bot.latency * 1000)} ms")

    async def _finalize_discord_start(self, ctx: discord.ApplicationContext):
        """Discord-only finalization: set guild name, send embed, capture IDs."""
        state_manager.set_discord_guild_name(ctx.guild.name)
        resp = await ctx.respond(embed=embed.server_status())
        msg_id = None
        if isinstance(resp, discord.Interaction):
            original_response = await resp.original_response()
            msg_id = original_response.id
        else:
            msg_id = resp.id
        state_manager.set_server_status_channel_and_msg_id(
            channel_id=ctx.channel_id,
            msg_id=msg_id
        )
        state_manager.save_to_file()
