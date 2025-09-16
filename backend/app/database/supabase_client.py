import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_ANON_KEY")

if not url or not key:
    raise EnvironmentError("Supabase URL and Key must be set in the environment variables.")

supabase: Client = create_client(url, key)
