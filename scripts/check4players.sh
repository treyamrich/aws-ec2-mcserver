#!/bin/bash
#Checks for active connections on  port 22 (ssh) and 25565 (minecraft)
#If no connections are found, the script gracefully shuts down the
#Minecraft server (saving progress) and then shuts down the Service
#This will stop the EC2 instance and save money.

while sleep 30m; do
        
        sshCons=$(netstat -anp | grep :22 | grep ESTABLISHED | wc -l)
        mcCons=$(netstat -anp | grep -E ":25565|:19132" | grep ESTABLISHED | wc -l)
        echo "Active SSH Connections: $sshCons"
        echo "Active Minecraft Connections: $mcCons"

        if [ $((mcCons)) = 0 ]
        then
                echo "We normally shutdown here, but let's check for SSH connections"
                if [[ $((sshCons)) = 0 ]]
                then
                        echo "no ssh connections, shutting down server"
                        bash /usr/bin/save-mcserver.sh
                        sudo shutdown
                else
                        echo "There are 1 or more active ssh connections, skip termination"
                fi
        else
                echo "Player Count: $mcCons"
        fi

done