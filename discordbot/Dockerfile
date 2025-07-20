FROM --platform=linux/amd64 python:3.9-slim

# Install pip
RUN python -m ensurepip --upgrade
RUN pip install py-cord boto3 mcstatus

RUN apt-get update && apt-get install -y nano curl docker.io

ENV DOCKER_CONFIG=/root/.docker

# Install Docker Compose
RUN mkdir -p $DOCKER_CONFIG/cli-plugins && \
    curl -SL "https://github.com/docker/compose/releases/download/v2.38.2/docker-compose-linux-x86_64" \
    -o $DOCKER_CONFIG/cli-plugins/docker-compose && \
    chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose

COPY bot /app/bot
COPY container-init.sh /app/container-init.sh

WORKDIR /app
RUN chmod +x ./container-init.sh
CMD ["./container-init.sh"]