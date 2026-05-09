import os
import httpx
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_KEY")

if not url or not key:
    raise EnvironmentError("Supabase URL and Service Key must be set in the environment variables.")

# Force HTTP/1.1 — HTTP/2 multiplexing causes "Server disconnected" errors
# in long-idle workers when Supabase closes the persistent connection.
supabase: Client = create_client(
    url,
    key,
    options=ClientOptions(
        httpx_client=httpx.Client(http2=False),
        postgrest_client_timeout=30,
        storage_client_timeout=30,
    ),
)

__all__ = ['supabase']

