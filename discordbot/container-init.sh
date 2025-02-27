#!/bin/bash

# Set up DuckDNS
source .env
echo url="https://www.duckdns.org/update?domains=$DUCK_DNS_DOMAIN&token=$DUCK_DNS_TOKEN&ip=" | curl -k -o duck.log -K -

python bot/src/bot.py