import discord
import ec2
import os
from util import config
from util.logger import Logger
from mcserver_status import mcserver

bot = discord.Bot(debug_guilds=config.DEBUG_GUILDS)

logger = Logger(os.path.basename(__file__), config.LOGGER_PATH, "debug")


async def _exception_helper(e: Exception, ctx):
    logger.error(e)
    if str(e) == "[Errno 8] nodename nor servname provided, or not known":
        await ctx.respond("Could not connect to minecraft server.")
    else:
        await ctx.respond("Error processing request.")


@bot.command(description="Starts the Minecraft server")
async def start(ctx):
    # Notify the guild that the server is starting.
    await ctx.respond(f"Processing request :robot:")

    # Attempt to start server
    instance = ec2.startServer()

    # Check request failure
    if len(instance.errors) > 0:
        await ctx.respond(
            "**Error:** Server failure. :cry: Please contact your administrator."
        )
        return

    # If server already running
    if not instance.isNew:
        await ctx.respond(f"The server is already running :yawning_face:")
        logger.debug(f"Server is already running at {config.SERVER_ADDRESS}")
        return

    desc = ":desktop: Server is booting up. Pls wait __5 min__ :pray:"
    logger.info("Server boot initiated")

    # Create embed response
    embed = discord.Embed(title=ctx.guild.name, description=desc, color=0x18CF9B)
    embed.add_field(
        name="Server Address", value=f"**{config.SERVER_ADDRESS}**", inline=False
    )
    embed.add_field(
        name="Server Notice",
        value="- The server will be automatically turned off if there are __0 players connections for 30 minutes__.\n- The server may also go down if Amazon decides to reclaim resources in the cloud. If this happens simply rerun the `/start` command and wait another 5 min.",
        inline=False,
    )
    embed.add_field(
        name="Server Map",
        value=f"http://dewcraft.duckdns.org:{config.SERVER_MAP_PORT}/",
    )
    embed.set_footer(
        text=f"Server hosted on AWS EC2. Instance Type: {instance.instanceType}"
    )
    # embed.set_image(url="https://play-lh.googleusercontent.com/VSwHQjcAttxsLE47RuS4PqpC4LT7lCoSjE7Hx5AW_yCxtDvcnsHHvm5CTuL5BPN-uRTP=w240-h480-rw")
    embed.set_thumbnail(
        url="https://img.icons8.com/plasticine/344/minecraft-grass-cube--v1.png"
    )
    await ctx.respond(embed=embed)


@bot.command(description="Lists number of players and ping.")
async def status(ctx):
    try:
        status = mcserver.list_status()
        instance = ec2.getServerInstance()
        instance_ip = instance.publicIp if instance else "Unknown"
        
        num_players, latency = status.players.online, int(status.latency)
        status_str = (
            f"There are {num_players} players online. Response in {latency} ms."
        )
        logger.debug(status_str)

        embed = discord.Embed(
            title=config.SERVER_ADDRESS, description="Server status", color=0x18CF9B
        )
        
        embed.add_field(name="Number of players", value=num_players)
        embed.add_field(name="Ping", value=f"{latency} ms")
        embed.add_field(
            name="Server Domain", value=f"**{config.SERVER_ADDRESS}**", inline=False
        )
        embed.add_field(
            name="Server IP Address", value=f"**{instance_ip}**", inline=False
        )
        await ctx.respond(embed=embed)
    except Exception as e:
        await _exception_helper(e, ctx)


@bot.command(description="Lists the connected players")
async def online_players(ctx):
    try:
        query = mcserver.list_players()
        players_str = ", ".join(query.players.names)
        player_list = query.players.names
        players_str = f"The server has the following players online: {players_str}"
        logger.debug(players_str)

        embed = discord.Embed(
            title=config.SERVER_ADDRESS, description="Server status", color=0x18CF9B
        )
        embed.add_field(name="Number of players", value=len(player_list))
        embed.add_field(name="Online Players", value="\n".join(player_list))
        await ctx.respond(embed=embed)
    except Exception as e:
        await _exception_helper(e, ctx)


@bot.command(description="Get the server's public IP address.")
async def ip(ctx):
    try:
        instance = ec2.getServerInstance()  
        instance_ip = instance.publicIp if instance else "Unknown"
        await ctx.respond(f"The server's public IP address is: {instance_ip}")
    except Exception as e:
        await _exception_helper(e, ctx)

@bot.command(description="Sends the bot's latency.")
async def ping(ctx):
    await ctx.respond(f"Pong! Latency is {int(bot.latency * 1000)} ms")


@bot.event
async def on_ready():
    logger.info(f"{bot.user.name} has connected to Discord!")


try:
    bot.run(config.TOKEN)
except Exception as e:
    logger.critical(e)
