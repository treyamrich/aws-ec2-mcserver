#!/bin/bash
# Script to be set in UserData section of AWS EC2 setup

S3_BUCKET_NAME=ec2-mc-server
SERVER_BACKUP=server-backup.tar.gz
INSTALL_PKG=install.tar.gz

TOKEN=`curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600"`
RESP=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" -s -w "%{http_code}" -o temp_output.txt http://169.254.169.254/latest/meta-data/instance-id)
INSTANCE_ID=$(<temp_output.txt)
HTTP_CODE=$RESP
rm temp_output.txt

if [ "$HTTP_CODE" -ne 200 ]; then
    echo "Failed to retrieve instance ID. Shutting down."
    shutdown -h now
fi

sudo yum update -y
sudo yum install -y docker

aws s3 cp s3://$S3_BUCKET_NAME/$SERVER_BACKUP $SERVER_BACKUP
aws s3 cp s3://$S3_BUCKET_NAME/$INSTALL_PKG $INSTALL_PKG

tar -xvf $SERVER_BACKUP # yields minecraft/
tar -xvf $INSTALL_PKG # yields dirs: build/ and scripts/

sudo service docker start
sudo systemctl enable docker.service

sudo docker build -t mc-server:latest -f build/Dockerfile .
sudo docker run -d \
  --name mc-server \
  --env-file build/.env \
  -e INSTANCE_ID=$INSTANCE_ID \
  -p 25565:25565 \
  --network host \
  -v ./minecraft:/app/minecraft \
  mc-server:latest