#!/bin/bash

docker rm -f mc-server
docker rmi mc-server:latest
docker build -t mc-server:latest -f build/Dockerfile .
docker run -d \
  --name mc-server \
  --env-file build/.env \
  -e LOCAL_DEV=true \
  -p 25565:25565 \
  --network host \
  -v ./minecraft:/app/minecraft \
  mc-server:latest
docker exec -it mc-server /bin/sh