import logging
import os
import sys
import threading
from typing import IO, Callable
import subprocess

class Logger:
    def __init__(self, name: str):
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s\n%(message)s\n')
        self.logger = logging.getLogger(name)
        
        c_handler = logging.StreamHandler(sys.stdout)
        c_handler.setFormatter(formatter)
        c_handler.setLevel(logging.INFO)
        
        c_error_handler = logging.StreamHandler(sys.stderr)
        c_error_handler.setFormatter(formatter)
        c_error_handler.setLevel(logging.WARNING)
        
        self.logger.addHandler(c_handler)
        self.logger.addHandler(c_error_handler)
        self.logger.setLevel(logging.INFO)
        self.c_handler = c_handler
        self.c_error_handler = c_error_handler
        
    def info(self, msg, **kwargs):
        self.logger.info(msg, **kwargs)
        
    def error(self, msg, **kwargs):
        self.logger.error(msg, **kwargs)
        
        
class TimedBuffer:
    def __init__(self, interval: float, log_fn: Callable[[str], None]):
        self.interval = interval
        self.log_fn = log_fn
        self.buffer = []
        self.lock = threading.Lock()
        self.timer = threading.Timer(self.interval, self.flush)
        self.timer.start()

    def add(self, line):
        with self.lock:
            self.buffer.append(line)

    def flush(self):
        with self.lock:
            if self.buffer:
                self.log_fn(''.join(self.buffer))
                self.buffer = []
        self.timer = threading.Timer(self.interval, self.flush)
        self.timer.start()

    def stop(self):
        self.timer.cancel()
        
def save_server(server_stdin: IO[str], logger: Logger):
    server_stdin.write("say SERVER SHUTTING DOWN IN 5 SECONDS. SAVING ALL MAPS...\n")
    server_stdin.write("save-all\n")
    server_stdin.write("stop\n")
    server_stdin.flush()
    try:
        subprocess.run(["/bin/sh", "/app/scripts/save-mcserver.sh"], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to execute save-mcserver.sh: {e}")
    
def shutdown_server(logger: Logger):
    try:
        subprocess.run(["aws", "ec2", "terminate-instances", "--instance-ids",  os.environ["INSTANCE_ID"]], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to terminate ec2 instance: {e}")