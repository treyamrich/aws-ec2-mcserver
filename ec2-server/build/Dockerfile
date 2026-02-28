FROM --platform=linux/arm64 alpine:latest

USER root
RUN apk add --no-cache curl python3 py3-pip supervisor aws-cli openjdk17-jdk
# RUN apk add --no-cache openjdk17-jdk

WORKDIR /app
RUN python3 -m venv /app/venv  && \
    /app/venv/bin/pip install --upgrade pip && \
    /app/venv/bin/pip install awscli

COPY service/supervisord.conf /etc/supervisord.conf

COPY scripts/ /app/scripts/
RUN chmod +x /app/scripts/*.sh

EXPOSE 25565/tcp
EXPOSE 19132/tcp

CMD ["/app/scripts/container-init.sh"]