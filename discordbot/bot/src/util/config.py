import configparser
import os
import sys

abs_path = os.path.dirname(os.path.abspath(__file__))
bot_dir = abs_path[:abs_path.find('src')]
config_path = os.path.join(bot_dir, 'conf', 'config.ini')
if not os.path.exists(config_path):
    sys.err("Error could not find config file.", file=sys.stderr)
    exit(1)

CONFIG_PATH_DISCORD = 'discord'
CONFIG_PATH_AWS = 'aws'
CONFIG_PATH_LOGGER = 'logger'
CONFIG_PATH_SERVER = 'server'

config = configparser.ConfigParser()
config.read(config_path)

def add_config(section, key, value):
    config[section][key] = value
    with open(config_path, "w") as configfile:
        config.write(configfile)

LOGGER_PATH = os.path.join(bot_dir, 'bot.log')

TOKEN = config.get(CONFIG_PATH_DISCORD, 'api-token')
DEBUG_GUILDS = [x for x in config.get(CONFIG_PATH_DISCORD, 'debug-guild-ids').split(',') if x != '']

SERVER_ADDRESS = config.get(CONFIG_PATH_SERVER, 'server-address')
SERVER_PORT_JAVA = config.get(CONFIG_PATH_SERVER, 'server-port-java')
SERVER_PORT_BEDROCK = config.get(CONFIG_PATH_SERVER, 'server-port-bedrock')
SERVER_MAP_PORT = config.get(CONFIG_PATH_SERVER, 'server-map-port')

SERVER_TAG = config.get(CONFIG_PATH_AWS, 'server-tag')
REGION = config.get(CONFIG_PATH_AWS, 'region')
LAUNCH_TEMPLATE_NAME = config.get(CONFIG_PATH_AWS, 'launch-template-name')