import logging

from core.config import config

class Logger:
    """
    This class encapsulates the logic for creating a logger using the python logging module.
    """
    def __init__(self, name: str):
        """
        name: name of the logger
        severity_level: str specifies the logging severity level. All log msgs of the level and above will be logged.
        """
        self.logger = logging.getLogger(name)
        self._set_log_level(config.GENERAL.log_level.value)

        base_format = '%(asctime)s - %(name)s  - %(levelname)s - %(message)s'
        # Conditional formatting
        class MethodFormatter(logging.Formatter):
            def format(self, record):
                if hasattr(record, 'method'):
                    self._style._fmt = '%(asctime)s - %(name)s - %(levelname)s - %(method)s - %(message)s'
                else:
                    self._style._fmt = base_format
                return super().format(record)
        formatter = MethodFormatter(base_format)
        
        c_handler = logging.StreamHandler()
        c_handler.setFormatter(formatter)
        self.logger.addHandler(c_handler)
        
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
            
    def debug(self, msg: str, **kwargs):
        self.logger.debug(msg, **kwargs)
    def info(self, msg: str, **kwargs):
        self.logger.info(msg, **kwargs)
    def warning(self, msg: str, **kwargs):
        self.logger.warning(msg, **kwargs)
    def error(self, msg: str, **kwargs):
        self.logger.error(msg, **kwargs)
    def critical(self, msg: str, **kwargs):
        self.logger.critical(msg, **kwargs)

    def log_with_info(self, func, func_name):
        """Logs the execution of the function.

        Args:
            func (function): A callback function to log and execute
        """
        log_str = f"Function: {func_name}"
        try:
            self.logger.info(log_str)
            res = func()
            self.logger.info(f"{log_str} - Message: SUCCESS")
            return res
        except Exception as e:
            self.logger.error(f"{log_str} - Message: {e})")
            raise e