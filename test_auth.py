import requests
import os
from dotenv import load_dotenv

# Load .env from backend folder
load_dotenv("backend/.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not ANON_KEY:
    print("❌ SUPABASE_URL or SUPABASE_ANON_KEY missing in backend/.env")
    exit(1)

print("=== Step 1: Login ===")
r = requests.post(
    f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
    headers={"apikey": ANON_KEY, "Content-Type": "application/json"},
    json={"email": "test@example.com", "password": "test1234"},
)

print(f"Status: {r.status_code}")
if r.status_code != 200:
    print(f"❌ Login failed")
    print(f"Response: {r.text}")
    exit(1)

data = r.json()
access_token = data["access_token"]
user_id = data["user"]["id"]
print(f"✅ Logged in")
print(f"Token: {access_token[:60]}...")
print(f"User ID: {user_id}")

print("\n=== Step 2: Test /me endpoint ===")
r = requests.get(
    "http://localhost:8000/me",
    headers={"Authorization": f"Bearer {access_token}"},
)

print(f"Status: {r.status_code}")
print(f"Response: {r.json()}")

if r.status_code == 200 and r.json().get("user_id") == user_id:
    print("\n✅ AUTH WORKS — token valid, /me returns your user_id")
else:
    print("\n❌ AUTH FAILED")