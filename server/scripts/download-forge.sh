sudo yum update -y
sudo yum install screen wget -y
wget --no-check-certificate -c --header "Cookie: oraclelicense=accept-securebackup-cookie" https://download.oracle.com/java/17/latest/jdk-17_linux-x64_bin.rpm
sudo rpm -Uvh jdk-17_linux-x64_bin.rpm 

cd /opt
sudo mkdir minecraft
sudo chown -R ec2-user:ec2-user minecraft
cd minecraft

aws s3 cp s3://minecraft-server/setup/forge-1.19-41.1.0-installer.jar .
java -jar forge-1.19-41.1.0-installer.jar --installServer
echo 'eula=true' > eula.txt

rm forge-1.19-41.1.0-installer.jar forge-1.19-41.1.0-installer.jar.log

#Change the RAM
#echo '-Xmx3G' > user_jvm_args.txt