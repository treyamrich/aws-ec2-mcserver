FROM --platform=linux/amd64 python:3.9-slim

# Install pip
RUN python -m ensurepip --upgrade
RUN pip install py-cord boto3 mcstatus

RUN apt-get update && apt-get install -y nano curl

RUN apt-get install -y docker.io

COPY bot /app/bot
COPY container-init.sh /app/container-init.sh

WORKDIR /app
RUN chmod +x ./container-init.sh
CMD ["./container-init.sh"]