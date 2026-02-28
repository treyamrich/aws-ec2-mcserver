import os
import select
import subprocess
import threading
from typing import IO
from util import Logger, TimedBuffer
import util

def print_server_output(fd: IO[str], fd_id: int, main_logger: Logger, server_logger: Logger, interval: float = 1.0):
    fd_name = "stderr" if fd_id == 2 else "stdout"
    log_fn = server_logger.error if fd_id == 2 else server_logger.info
    buffer = TimedBuffer(interval, log_fn)
    main_logger.info(f"{fd_name} printing thread started")
    try:
        for line in iter(fd.readline, ''):
            buffer.add(line)
    finally:
        buffer.stop()
        main_logger.info(f"Server closed {fd_name}")

def cmd_handler(pipe_name: str, stdin: IO[str]):
    logger = Logger("CMDHandler")
    try:
        with open(pipe_name, 'r') as pipe:
            while True:
                rlist, _, _ = select.select([pipe], [], [])
                if pipe in rlist:
                    line = pipe.readline()
                    line_stripped = line.strip()
                    if line_stripped == "exit()": 
                        break
                    if line_stripped == "saveAndTerminate()":
                        util.save_server(stdin, logger)
                        util.shutdown_server(logger)
                        break
                    if line:
                        logger.info(f"Forwarding command to server: '{line_stripped}'")
                        stdin.write(line)
                        stdin.flush()
    except Exception as e:
        logger.error(f"Error reading from pipe: {e}")
    finally:
        logger.info(f"{pipe_name} closed")
        stdin.close()
def main():
    pipe_name = "/tmp/mcserver"
    logger = Logger("main")
    server_logger = Logger("MCServer")
    logger.info(f"{__file__} started")
                
    try:
        # Create the named pipe if it doesn't exist
        if not os.path.exists(pipe_name):
            os.mkfifo(pipe_name)

        cmd = ["./start.sh"]
    
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd="/app/minecraft")
        stdout_thread = threading.Thread(target=print_server_output, args=(process.stdout, 1, logger, server_logger))
        stdout_thread.start()
        stderr_thread = threading.Thread(target=print_server_output, args=(process.stderr, 2, logger, server_logger))
        stderr_thread.start()
        stdin_thread = threading.Thread(target=cmd_handler, args=(pipe_name, process.stdin))
        stdin_thread.start()
    finally:
        process.wait()
        stdout_thread.join()
        stderr_thread.join()
        
        # This will only be ran if the subproc terminated
        # It should not be sent from external processes, otherwise pipes to the server will be lost
        with open(pipe_name, 'w') as pipe:
            pipe.write("exit()")
            pipe.flush()
            
        stdin_thread.join()
        logger.info(f"{__file__} exiting")

if __name__ == "__main__":
    main()
