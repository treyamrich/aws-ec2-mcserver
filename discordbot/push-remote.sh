#!/bin/bash

docker build -t mc-server-discord-bot:latest .
docker save -o image.tar mc-server-discord-bot:latest && gzip -f image.tar
scp -i $1 image.tar.gz ec2-user@$2:~/

# On remote server - If aws creds can't be fetched in container, ensure role assumption works and check if token hop is 2 b/c of docker -> localhost -> aws IDMSv2
# sudo docker rm -f discord-bot && gunzip image.tar.gz && sudo docker load -i image.tar && rm image.tar && sudo docker run -d --name discord-bot mc-server-discord-bot:latest