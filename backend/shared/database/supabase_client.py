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
        httpx_client=httpx.Client(
            http2=False,
            # Short connect timeout — fail fast on stalled TCP handshakes
            # (common when ForkPoolWorkers inherit a shared connection pool)
            timeout=httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0),
            # Sized for gunicorn gthread workers (16 threads per process).
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        ),
        postgrest_client_timeout=30,
        storage_client_timeout=30,
    ),
)




# The API returns at most 1000 rows per request (Supabase "max rows"), whatever
# .limit() asks for. Anything that can grow past that has to page.
PAGE_SIZE = 1000


def fetch_all(make_query, page_size: int = PAGE_SIZE, max_rows: int = 200_000) -> list[dict]:
    """
    All rows of a query, fetched page by page.

    make_query: a function returning a fresh, ordered query, e.g.
        lambda: supabase.table("tenant_sources").select("id").eq("tenant_id", t).order("id")
    The order keeps pages stable while rows are being added.
    """
    rows: list[dict] = []
    while len(rows) < max_rows:
        page = make_query().range(len(rows), len(rows) + page_size - 1).execute().data or []
        rows += page
        if len(page) < page_size:
            break
    return rows


__all__ = ['supabase', 'fetch_all']
