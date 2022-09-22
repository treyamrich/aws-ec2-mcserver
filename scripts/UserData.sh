#!/bin/bash

sudo yum update -y
sudo yum install screen wget -y
wget --no-check-certificate -c --header "Cookie: oraclelicense=accept-securebackup-cookie" https://download.oracle.com/java/17/latest/jdk-17_linux-x64_bin.rpm
sudo rpm -Uvh jdk-17_linux-x64_bin.rpm 

#Get server folder and setup scripts/service files from s3
sudo aws s3 cp s3://trey-minecraft-server/medievalmc-server-backup.tar.gz .
sudo aws s3 cp s3://trey-minecraft-server/setup/services/minecraft.service /etc/systemd/system
sudo aws s3 cp s3://trey-minecraft-server/setup/services/spot-interrupt.service /etc/systemd/system
sudo aws s3 cp s3://trey-minecraft-server/setup/services/check-players.service /etc/systemd/system
sudo aws s3 cp s3://trey-minecraft-server/setup/scripts/save-mcserver.sh /usr/bin
sudo aws s3 cp s3://trey-minecraft-server/setup/scripts/checkinterrupt.sh /usr/bin
sudo aws s3 cp s3://trey-minecraft-server/setup/scripts/check4players.sh /usr/bin

#Unzip server folder and change ownership
sudo tar -xvf medievalmc-server-backup.tar.gz -C /opt
sudo chown -R ec2-user:ec2-user /opt/minecraft
sudo chmod +x /usr/bin/save-mcserver.sh
sudo chmod +x /usr/bin/checkinterrupt.sh
sudo chmod +x /usr/bin/check4players.sh

#Update DDNS
mkdir ~/duckdns
sudo chmod ugo+rw ~/duckdns
cd ~/duckdns
echo url="https://www.duckdns.org/update?domains=dewcraft&token=MY_DUCKDNS_TOKEN_HERE&ip=" | curl -k -o ~/duckdns/duck.log -K -

#Start the services
sudo systemcl daemon-reload
sudo service minecraft start
sudo service spot-interrupt start
sudo service check-players start
