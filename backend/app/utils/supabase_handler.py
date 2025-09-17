import logging
import traceback
from app.database.supabase_client import supabase

class SupabaseHandler(logging.Handler):
    """
    A custom logging handler that sends log records to a Supabase table.
    """
    def emit(self, record):
        """
        Formats and sends a log record to the 'app_logs' table in Supabase.
        """
        try:
            # Extract traceback information if the record contains an exception
            trace = None
            if record.exc_info:
                trace = "".join(traceback.format_exception(*record.exc_info))

            # Prepare the data payload for Supabase
            payload = {
                'level': record.levelname,
                'message': record.getMessage(),
                'traceback': trace,
                'path': record.pathname,
                'lineno': record.lineno,
            }

            # Add user_id if it's passed in the 'extra' dictionary during the log call
            if hasattr(record, 'user_id'):
                payload['user_id'] = str(record.user_id)

            # Insert the log record into the 'app_logs' table
            supabase.table('app_logs').insert(payload).execute()

        except Exception:
            # If logging to Supabase fails for any reason, we fall back to
            # writing to stderr to avoid an infinite logging loop.
            # This is a critical safety measure.
            import sys
            sys.stderr.write("--- CRITICAL: Logging to Supabase failed! ---\n")
            sys.stderr.write(self.format(record) + "\n")
            sys.stderr.write("--- END OF FAILED LOG ---\n")
