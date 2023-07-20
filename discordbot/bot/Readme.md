# Setup

## AWS

### IAM policy
Create an policy that allows:
- creating spot fleet instances
- access to your aws s3 bucket that will store the minecraft server files
- run ec2 instances

### EC2
1. Go to ec2 on the aws management console. 
2. Start up an ec2 instance (t2.micro is free) and attach the role you created so that spot instances can be created.

### Launch Template
When you create a spot fleet request, you must specify a launch template.
In the template:
1. Select the key pair that you created in the EC2 section of this document
2. Choose the images you want to be launched
3. Choose the iam role that you created
4. Copy your UserData.sh script to be ran on instance creation

## Docker

### Export image
1. In the `discordbot` directory run `docker build -t mc-server-discord-bot:latest .`
    This will create an image from the dockerfile.
2. Run `docker save -o image.tar mc-server-discord-bot:latest`
    This will compress the image into a tar archive.
3. Transfer the image from your local computer to your AWS ec2 instance by running `scp -i /path/to/ssh-certificate.pem image.tar ec2-user@ec2-instance-ip-address:~/`
    Fill in the path to the ssh certificate you downloaded when setting up your ec2 instance.
    Fill in the ip address or domain (if you set up duckdns in the script /discordbot/UserData.sh)
4. ssh into your AWS ec2 instance and load the image into docker from the tar file: `sudo docker load -i image.tar`
5. Run the container and get a bash shell: `sudo docker run -it mc-server-discord-bot:latest /bin/bash`

### Configuration
Once you have a shell in the docker container (from the section above), you can configure the bot by going to the bot folder: `cd /app/bot/`
Open `nano config.ini` and set your:
- discord api token (**required**)
- server tag (optional)
- server domain (optional)

### Run 
Start the docker container on AWS ec2 with the bot script.
`sudo docker run -d mc-server-discord-bot:latest python /app/bot/bot.py`