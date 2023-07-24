import logging

class Logger:
    """
    This class encapsulates the logic for creating a logger using the python logging module.
    """
    def __init__(self, name: str, file_output_path: str, severity_level: str = 'warning'):
        """
        name: name of the logger
        severity_level: str specifies the logging severity level. All log msgs of the level and above will be logged.
        """
        self.logger = logging.getLogger(name)
        self._set_log_level(severity_level)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        c_handler = logging.StreamHandler()
        c_handler.setFormatter(formatter)
        self.logger.addHandler(c_handler)
        
        try:
            f_handler = logging.FileHandler(file_output_path)
            f_handler.setFormatter(formatter)
            self.logger.addHandler(f_handler)
        except FileNotFoundError as e:
            self.logger.warning(e)
        
    def _set_log_level(self, severity_level: str):
        if severity_level == 'debug':
            self.logger.setLevel(logging.DEBUG)
        elif severity_level == 'info':
            self.logger.setLevel(logging.INFO)
        elif severity_level == 'error':
            self.logger.setLevel(logging.ERROR)
        elif severity_level == 'critical':
            self.logger.setLevel(logging.CRITICAL)
        else: # Default level
            self.logger.setLevel(logging.WARNING)
            
    def debug(self, msg: str):
        self.logger.debug(msg)
    def info(self, msg: str):
        self.logger.info(msg)
    def warning(self, msg: str):
        self.logger.warning(msg)
    def error(self, msg: str):
        self.logger.error(msg)
    def critical(self, msg: str):
        self.logger.critical(msg)
    
    def log_with_info(self, func, func_name):
        """Logs the execution of the function.

        Args:
            func (function): A callback function to log and execute
        """
        log_str = f"Function: {func_name} - Message: "
        try:
            self.logger.info(log_str)
            res = func()
            self.logger.info(log_str + "SUCCESS")
            return res
        except Exception as e:
            self.logger.error(log_str + f"{e})")
            raise e