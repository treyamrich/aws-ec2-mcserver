#!/bin/sh

# Get total memory in MB
total_mem=$(free -m | awk '/^Mem:/{print $2}')

# Set default values
xmx="7G"
xms="4G"

# Adjust Xmx based on total memory
if [ "$total_mem" -ge 16000 ]; then
    xmx="15G"
fi

echo -e "-Xmx$xmx\n-Xms$xms" > user_jvm_args.txt

"java" -javaagent:log4jfix/Log4jPatcher-1.0.0.jar -XX:+UseG1GC -XX:+UnlockExperimentalVMOptions -Xmx6144M -Xms4096M @user_jvm_args.txt @libraries/net/minecraftforge/forge/1.18.2-40.2.14/unix_args.txt nogui