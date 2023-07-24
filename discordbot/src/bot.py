import discord
import ec2
import os
from util import config
from util.logger import Logger
import mcserver_status as mcserver

logger = Logger(os.path.basename(__file__), config.LOGGER_PATH,'debug')
mcserver_builder = mcserver.MinecraftServerBuilder(
    config.SERVER_ADDRESS, 
    config.SERVER_PORT_JAVA
)

bot = discord.Bot()

@bot.command(description="Starts the Minecraft server")
async def start(ctx):
	#Notify the guild that the server is starting.
	await ctx.respond(f'Processing request :robot:')
	
	#Attempt to start server
	instance = ec2.startServer()

	#Check request failure
	if len(instance.errors) > 0:
		await ctx.respond('**Error:** Server failure. :cry: Please contact your administrator.')
		return

	#If server already running
	if not instance.isNew:
		desc = "The server is already running :yawning_face:"
		logger.debug(f"Server is already running at **{config.SERVER_ADDRESS}**")
		return

	desc = ":desktop: Server is booting up. Pls wait __5 min__ :pray:"
	logger.info("Server boot initiated")

	#Create embed response
	embed = discord.Embed(
		title=ctx.guild.name,
		description=desc,
		color=0x18CF9B
	)
	embed.add_field(name="Server Address", value=f"**{config.SERVER_ADDRESS}**", inline=False)
	embed.add_field(name="Server Notice", value="- The server will be automatically turned off if there are __0 players connections for 30 minutes__.\n- The server may also go down if Amazon decides to reclaim resources in the cloud. If this happens simply rerun the `/start` command and wait another 5 min.", inline=False)
	embed.add_field(name="Server Map", value=f"http://dewcraft.duckdns.org:{config.SERVER_MAP_PORT}/")
	embed.set_footer(text=f"Server hosted on AWS EC2. Instance Type: {instance.instanceType}")
	#embed.set_image(url="https://play-lh.googleusercontent.com/VSwHQjcAttxsLE47RuS4PqpC4LT7lCoSjE7Hx5AW_yCxtDvcnsHHvm5CTuL5BPN-uRTP=w240-h480-rw")
	embed.set_thumbnail(url="https://img.icons8.com/plasticine/344/minecraft-grass-cube--v1.png")
	await ctx.respond(embed=embed)
  
@bot.command(description="Lists the connected players")
async def list_players(ctx):
	try:
		server = mcserver_builder.build_java_server()
		status = server.list_status()
		online_players = status.players.online
		await ctx.respond(f"Online players: {online_players}")
	except Exception as e:
		logger.error(f"An error occurred: {str(e)}")
		await ctx.respond(f"**Error fetching online player list**")

@bot.command(description="Sends the bot's latency.")
async def ping(ctx):
    await ctx.respond(f"Pong! Latency is {int(bot.latency * 1000)} ms")

@bot.event
async def on_ready():
    logger.info(f'{bot.user.name} has connected to Discord!')

try:
    bot.run(config.TOKEN)
except Exception as e:
    logger.critical(e)
