#!/bin/sh
#Checks for active connections on  port 22 (ssh) and 25565 (minecraft)
#If no connections are found, the script gracefully shuts down the
#Minecraft server (saving progress) and then shuts down the Service
#This will stop the EC2 instance and save money.

timer_start=0
timer_running=false

check_connections() {
        time_limit=15
        sshCons=$(netstat -an | grep :22 | grep ESTABLISHED | wc -l)
        mcCons=$(netstat -an | grep -E ":25565|:19132" | grep ESTABLISHED | wc -l)
        totalCons=$((sshCons + mcCons))
        echo "Active SSH Connections: $sshCons"
        echo "Active Minecraft Connections: $mcCons"

        if [ $totalCons -eq 0 ]; then
                if [ "$timer_running" = false ]; then
                        timer_start=$(date +%s)
                        timer_running=true
                        echo "No connections found. Timer started."
                else
                        current_time=$(date +%s)
                        elapsed_time=$(( (current_time - timer_start) / 60 ))
                        echo "Timer running. Elapsed time: $elapsed_time minutes."
                        if [ $elapsed_time -ge $time_limit ]; then
                                echo "No connections for $time_limit minutes. Shutting down server."
                                echo "saveAndTerminate()" > /tmp/mcserver
                        fi
                fi
        else
                if [ "$timer_running" = true ]; then
                        echo "Connections detected. Stopping and resetting timer."
                        timer_running=false
                        timer_start=0
                fi
        fi
}

while sleep 1m; do
        check_connections
done