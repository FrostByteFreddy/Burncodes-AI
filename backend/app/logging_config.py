import logging
import os
from logging.handlers import TimedRotatingFileHandler

def setup_logging():
    """Sets up a timed rotating file logger for error messages."""
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger('api_error_logger')
    logger.setLevel(logging.ERROR)

    # Prevent adding handlers multiple times in case of reloads
    if logger.hasHandlers():
        return logger

    # Rotates the log file every hour, keeps 24 backups
    handler = TimedRotatingFileHandler(
        os.path.join(log_dir, 'error.log'),
        when='H',
        interval=1,
        backupCount=24
    )

    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s [in %(pathname)s:%(lineno)d]'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

# Global logger instance to be imported by other modules
error_logger = setup_logging()
