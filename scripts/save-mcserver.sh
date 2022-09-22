#!/bin/bash

cd /opt

#Zip server and upload
sudo tar -cpvzf medievalmc-server-backup.tar.gz minecraft
aws s3 cp medievalmc-server-backup.tar.gz s3://trey-minecraft-server
