#!/bin/bash

# Load Discord API token from file if DISCORD_API_TOKEN_FILE is set
if [ -n "$DISCORD_API_TOKEN_FILE" ] && [ -f "$DISCORD_API_TOKEN_FILE" ]; then
    export DISCORD_API_TOKEN=$(cat "$DISCORD_API_TOKEN_FILE")
fi

# Set up DuckDNS (only for deployments with DNS tokens configured)
if [ "$DEPLOYMENT" != "local" ] && [ -n "$DUCK_DNS_DOMAIN" ] && [ -n "$DUCK_DNS_TOKEN" ]; then
    echo url="https://www.duckdns.org/update?domains=$DUCK_DNS_DOMAIN&token=$DUCK_DNS_TOKEN&ip=" | curl -k -o duck.log -K - || true
fi

python bot/src/main.py
