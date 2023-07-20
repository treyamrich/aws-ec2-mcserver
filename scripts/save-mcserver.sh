#!/bin/bash

SERVER_BACKUP="mc-server-backup.tar.gz"

cd /opt

#Zip server and upload
sudo tar -cpvzf $SERVER_BACKUP minecraft
aws s3 cp $SERVER_BACKUP s3://trey-minecraft-server
