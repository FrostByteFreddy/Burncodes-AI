import logging
from app.utils.supabase_handler import SupabaseHandler

def setup_logging():
    """Sets up a logger to send errors to Supabase."""
    logger = logging.getLogger('api_error_logger')
    logger.setLevel(logging.ERROR)

    # Prevent adding handlers multiple times in case of reloads,
    # which can happen in a development environment like Flask's.
    if logger.hasHandlers():
        return logger

    # Use our custom Supabase handler
    handler = SupabaseHandler()
    logger.addHandler(handler)

    return logger

# Global logger instance to be imported by other modules
error_logger = setup_logging()
