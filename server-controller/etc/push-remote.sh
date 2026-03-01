#!/bin/bash

etc/build.sh ec2 discord
IMAGE="mc-server-controller:ec2-discord"
docker save -o image.tar "$IMAGE" && gzip -f image.tar
scp -i $1 image.tar.gz ec2-user@$2:~/

# On remote server - If aws creds can't be fetched in container, ensure role assumption works and check if token hop is 2 b/c of docker -> localhost -> aws IDMSv2
# sudo docker rm -f discord-bot && gunzip image.tar.gz && sudo docker load -i image.tar && rm image.tar && sudo docker run -d --name discord-bot mc-server-discord-bot:latest