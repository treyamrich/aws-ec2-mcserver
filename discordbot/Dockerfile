FROM --platform=linux/amd64 python:3.9-slim

# Install pip
RUN python -m ensurepip --upgrade
RUN pip install py-cord boto3 mcstatus

RUN apt-get update && apt-get install -y nano curl

COPY bot /app/bot
COPY container-init.sh /app/container-init.sh
# Proper .env files must start with #.env
COPY .env /app/.env

WORKDIR /app
RUN chmod +x ./container-init.sh
CMD ["./container-init.sh"]