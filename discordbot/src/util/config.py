import configparser
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir[:script_dir.find('src')], 'conf', 'config.ini')
if not os.path.exists(config_path):
    print("Error could not find config file.")
    exit(1)
    
CONFIG_PATH_DISCORD = 'discord'
CONFIG_PATH_AWS = 'aws'
CONFIG_PATH_LOGGER = 'logger'
CONFIG_PATH_SERVER = 'server'

config = configparser.ConfigParser()
config.read(config_path)

LOGGER_PATH = config.get(CONFIG_PATH_LOGGER, 'log-file-path')

TOKEN = config.get(CONFIG_PATH_DISCORD, 'api-token')

SERVER_ADDRESS = config.get(CONFIG_PATH_SERVER, 'server-address')
SERVER_PORT_JAVA = config.get(CONFIG_PATH_SERVER, 'server-port-java')
SERVER_PORT_BEDROCK = config.get(CONFIG_PATH_SERVER, 'server-port-bedrock')
SERVER_MAP_PORT = config.get(CONFIG_PATH_SERVER, 'server-map-port')

SERVER_TAG = config.get(CONFIG_PATH_AWS, 'server-tag')
REGION = config.get(CONFIG_PATH_AWS, 'region')
LAUNCH_TEMPLATE_NAME = config.get(CONFIG_PATH_AWS, 'launch-template-name')