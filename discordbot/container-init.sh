#!/bin/bash

# Set up DuckDNS (only for deployments with DNS tokens configured)
if [ "$DEPLOYMENT" != "local" ] && [ -n "$DUCK_DNS_DOMAIN" ] && [ -n "$DUCK_DNS_TOKEN" ]; then
    echo url="https://www.duckdns.org/update?domains=$DUCK_DNS_DOMAIN&token=$DUCK_DNS_TOKEN&ip=" | curl -k -o duck.log -K - || true
fi

python bot/src/main.py
