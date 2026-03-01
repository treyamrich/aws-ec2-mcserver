#!/usr/bin/env bash
# Script to be set in UserData section of AWS EC2 setup

sudo yum update -y

#Install docker
sudo yum install -y docker
sudo service docker start
sudo systemctl enable docker.service