import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_KEY")

if not url or not key:
    raise EnvironmentError("Supabase URL and Service Key must be set in the environment variables.")

bucket_name: str = os.environ.get("SUPABASE_BUCKET_NAME")
if not bucket_name:
    raise EnvironmentError("Supabase bucket name must be set in the environment variables.")

supabase: Client = create_client(url, key)

# Export the bucket name for use in other parts of the application
__all__ = ['supabase', 'bucket_name']
