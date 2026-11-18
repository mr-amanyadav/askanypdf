import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from config import SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_ANON_KEY

print(f"URL: {SUPABASE_URL}")
print(f"Anon key starts with: {SUPABASE_ANON_KEY[:20]}... (len={len(SUPABASE_ANON_KEY)})")
print(f"Service key starts with: {SUPABASE_SERVICE_KEY[:20]}... (len={len(SUPABASE_SERVICE_KEY)})")

if SUPABASE_ANON_KEY == SUPABASE_SERVICE_KEY:
    print("❌ ERROR: anon and service keys are identical! Wrong.")
    exit(1)

from supabase import create_client
try:
    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    # Try a real operation
    result = client.table("documents").select("id").limit(1).execute()
    print(f"✅ Service client works — queried documents table, got {len(result.data)} rows")
except Exception as e:
    print(f"❌ Failed: {e}")