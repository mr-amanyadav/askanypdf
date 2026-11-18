from supabase import create_client, Client
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY


def get_service_client() -> Client:
    """Admin client — bypasses RLS. Only use after auth checks."""
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def get_anon_client() -> Client:
    """Anonymous client — respects RLS."""
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)