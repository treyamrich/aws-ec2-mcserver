#!/bin/sh

# Set up DuckDNS
if [ "$LOCAL_DEV" != true ]; then
    echo url="https://www.duckdns.org/update?domains=$DUCK_DNS_DOMAIN&token=$DUCK_DNS_TOKEN&ip=" | curl -k -o duck.log -K -
fi

supervisord -c "/etc/supervisord.conf"