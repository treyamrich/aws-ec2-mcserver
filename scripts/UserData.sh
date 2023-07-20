#!/bin/bash

DUCK_DNS_DOMAIN="dewcraft"
DUCK_DNS_TOKEN="de1d7258-a68d-4532-9e25-5973f79946ec"

SERVER_BACKUP="mc-server-backup.tar.gz"

#Update DDNS
mkdir ~/duckdns
sudo chmod ugo+rw ~/duckdns
cd ~/duckdns
echo url="https://www.duckdns.org/update?domains=$DUCK_DNS_DOMAIN&token=$DUCK_DNS_TOKEN&ip=" | curl -k -o ~/duckdns/duck.log -K -

sudo yum update -y
sudo yum install screen wget -y
wget --no-check-certificate -c --header "Cookie: oraclelicense=accept-securebackup-cookie" https://download.oracle.com/java/17/latest/jdk-17_linux-x64_bin.rpm
sudo rpm -Uvh jdk-17_linux-x64_bin.rpm 

#Get server folder and setup scripts/service files from s3
sudo aws s3 cp s3://trey-minecraft-server/$SERVER_BACKUP .
sudo aws s3 cp s3://trey-minecraft-server/setup/services/minecraft.service /etc/systemd/system
sudo aws s3 cp s3://trey-minecraft-server/setup/services/spot-interrupt.service /etc/systemd/system
sudo aws s3 cp s3://trey-minecraft-server/setup/services/check-players.service /etc/systemd/system
sudo aws s3 cp s3://trey-minecraft-server/setup/scripts/save-mcserver.sh /usr/bin
sudo aws s3 cp s3://trey-minecraft-server/setup/scripts/checkinterrupt.sh /usr/bin
sudo aws s3 cp s3://trey-minecraft-server/setup/scripts/check4players.sh /usr/bin

#Unzip server folder and change ownership
sudo tar -xvf $SERVER_BACKUP -C /opt
sudo chown -R ec2-user:ec2-user /opt/minecraft
sudo chmod +x /usr/bin/save-mcserver.sh
sudo chmod +x /usr/bin/checkinterrupt.sh
sudo chmod +x /usr/bin/check4players.sh

#Start the services
sudo systemcl daemon-reload
sudo service minecraft start
sudo service spot-interrupt start
sudo service check-players start
