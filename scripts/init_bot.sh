#!/usr/bin/env bash
sudo yum update -y
sudo yum groupinstall "Development Tools" -y
sudo yum install openssl11 openssl11-devel  libffi-devel bzip2-devel wget -y
wget https://www.python.org/ftp/python/3.10.4/Python-3.10.4.tgz
tar -xf Python-3.10.4.tgz
cd Python-3.10.4/
./configure --enable-optimizations
make -j $(nproc)
sudo make altinstall
sudo yum install python3-pip
python3.10 -m pip install -U py-cord 
python3.10 -m pip install -U python-dotenv
python3.10 -m pip install -U boto3
python3.10 bot.py