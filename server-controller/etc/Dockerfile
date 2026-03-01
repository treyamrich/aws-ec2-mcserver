FROM python:3.13-slim

ARG DEPLOY_STRATEGY=local
ARG STARTER=discord

# Install requirements based on starter type
COPY etc/requirements-discord.txt /app/etc/requirements-discord.txt
COPY etc/requirements-http.txt /app/etc/requirements-http.txt
RUN if [ "$STARTER" = "http" ]; then \
        pip install -r /app/etc/requirements-http.txt; \
    else \
        pip install -r /app/etc/requirements-discord.txt; \
    fi

# Install system packages based on deploy strategy
RUN if [ "$DEPLOY_STRATEGY" = "local" ]; then \
        apt-get update && apt-get install -y nano curl docker.io && \
        DOCKER_CONFIG=/root/.docker && \
        mkdir -p $DOCKER_CONFIG/cli-plugins && \
        curl -SL "https://github.com/docker/compose/releases/download/v2.38.2/docker-compose-linux-x86_64" \
            -o $DOCKER_CONFIG/cli-plugins/docker-compose && \
        chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose; \
    else \
        apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*; \
    fi

ENV DOCKER_CONFIG=/root/.docker
ENV DEPLOYMENT=${DEPLOY_STRATEGY}
ENV STARTER=${STARTER}

COPY bot /app/bot
COPY etc/container-init.sh /app/container-init.sh

WORKDIR /app
RUN chmod +x ./container-init.sh
CMD ["./container-init.sh"]
