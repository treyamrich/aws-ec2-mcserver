#!/usr/bin/env bash

DUCK_DNS_TOKEN="de1d7258-a68d-4532-9e25-5973f79946ec"
DUCK_DNS_DOMAIN="tradernib"

sudo yum update -y

#Install docker
sudo yum install -y docker
sudo service docker start
sudo systemctl enable docker.service

#Update DDNS
mkdir ~/duckdns
sudo chmod ugo+rw ~/duckdns
cd ~/duckdns
echo url="https://www.duckdns.org/update?domains=$DUCK_DNS_DOMAIN&token=$DUCK_DNS_TOKEN&ip=" | curl -k -o ~/duckdns/duck.log -K -

#To run the bot go to the Readme.md and read how to setup the docker container