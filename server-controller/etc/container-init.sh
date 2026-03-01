#!/bin/bash

# Set up DuckDNS when configured (any deployment)
if [ -n "$DUCK_DNS_DOMAIN" ] && [ -n "$DUCK_DNS_TOKEN" ]; then
    echo url="https://www.duckdns.org/update?domains=$DUCK_DNS_DOMAIN&token=$DUCK_DNS_TOKEN&ip=" | curl -k -o duck.log -K - || true
fi

# Load Discord API token from file (only for discord starter)
if [ "$STARTER" != "http" ]; then
    if [ -n "$DISCORD_API_TOKEN_FILE" ] && [ -f "$DISCORD_API_TOKEN_FILE" ]; then
        export DISCORD_API_TOKEN=$(cat "$DISCORD_API_TOKEN_FILE")
    fi
fi

# Load HTTP API token from file (only for http starter)
if [ "$STARTER" = "http" ]; then
    if [ -n "$HTTP_API_TOKEN_FILE" ] && [ -f "$HTTP_API_TOKEN_FILE" ]; then
        export HTTP_API_TOKEN=$(cat "$HTTP_API_TOKEN_FILE")
    fi
fi

# Branch on STARTER
if [ "$STARTER" = "http" ]; then
    python bot/src/http_server.py
else
    python bot/src/discord_bot.py
fi
