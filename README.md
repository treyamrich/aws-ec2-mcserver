# aws-ec2-mcserver
Utilizing AWS EC2 Spot Fleet to reduce cost and host a modded Minecraft server.

# Navigating folder structure
This project has separate folders that contain scripts, service files and python files.

* /discordbot contains files for running the discord bot and the aws boto3 api calls.
* /scripts contains scripts that are run via service files and utility scripts for downloading packages.
* /services contains service files to run minecraft, to check the player connections and to save the world file.

# About this repo
This repository contains files that can be used to run a Minecraft server on AWS EC2, using AWS boto3 to make Spot Fleet requests.
The server automatically shuts down by checking if players are connected every 30 minutes.
The server automatically checks for instance interruptions as well. 
Either the case, backups are stored on AWS S3.
