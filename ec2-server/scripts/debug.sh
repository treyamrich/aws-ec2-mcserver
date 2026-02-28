# Debugging server.py paste this into a file minecraft/start.sh
# while true
# do 
#     if read -t 10 input; then
#         echo "Current time: $(date)"
#         echo "Input received: $input"
#         echo "Input received to error: $input" 1>&2
#     fi
# done