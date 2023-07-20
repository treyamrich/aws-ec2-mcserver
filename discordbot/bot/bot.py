import discord
import ec2
from config import config
import logging 

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

TOKEN = config.get('discord', 'api-token')
DOMAIN = config.get('aws', 'server-domain')

SERVER_ADDRESS = config.get('mc-server', 'server-address')
SERVER_PORT = config.get('mc-server', 'server-port')

#Initialize bot
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
		logging.info("Server is already running")
	else:
		desc = ":desktop: Server is booting up. Pls wait __5 min__ :pray:"
		logging.info("Server boot initiated")
	
	#Create embed response
	embed = discord.Embed(
		title=ctx.guild.name,
		description=desc,
		color=0x18CF9B
	)
	embed.add_field(name="Server Domain", value=f"**{DOMAIN}**", inline=False)
	embed.add_field(name="Server Notice", value="- The server will be automatically turned off if there are __0 players connections for 30 minutes__.\n- The server may also go down if Amazon decides to reclaim resources in the cloud. If this happens simply rerun the `/start` command and wait another 5 min :sweat_smile:", inline=False)
	embed.set_footer(text=f"Server hosted on AWS EC2. Instance Type: {instance.instanceType}")
	embed.set_image(url="https://play-lh.googleusercontent.com/VSwHQjcAttxsLE47RuS4PqpC4LT7lCoSjE7Hx5AW_yCxtDvcnsHHvm5CTuL5BPN-uRTP=w240-h480-rw")
	embed.set_thumbnail(url="https://img.icons8.com/plasticine/344/minecraft-grass-cube--v1.png")
	await ctx.respond(embed=embed)

@bot.command(description="Lists the connected players")
async def list_players(ctx):
	try:
		online_players = status.players.online
		logging.info(f"Executed list_players. Online players: {online_players}")
		await ctx.respond(f"Online players: {online_players}")
	except Exception as e:
		logging.error(f"An error occurred: {str(e)}")
		await ctx.respond(f"**Error fetching online player list**")

@bot.command(description="Sends the bot's latency.")
async def ping(ctx):
    await ctx.respond(f"Pong! Latency is {int(bot.latency * 1000)} ms")

@bot.event
async def on_ready():
    logging.info(f'{bot.user.name} has connected to Discord!')

bot.run(TOKEN)
