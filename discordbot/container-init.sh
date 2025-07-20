#!/bin/bash

# Set up DuckDNS
if [ "$DEPLOYMENT" != "local" ]; then
    echo url="https://www.duckdns.org/update?domains=$DUCK_DNS_DOMAIN&token=$DUCK_DNS_TOKEN&ip=" | curl -k -o duck.log -K -
fi

python bot/src/main.py