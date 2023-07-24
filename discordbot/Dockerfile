FROM --platform=linux/amd64 python:3.9-slim

# Install pip
RUN python -m ensurepip --upgrade
RUN pip install py-cord boto3 mcstatus

RUN apt-get update && apt-get install -y nano

COPY bot /app/bot

WORKDIR /app
CMD ["python", "bot/src/bot.py"]