import requests
import os
import time
from dotenv import load_dotenv

load_dotenv("backend/.env")
SUPABASE_URL = os.getenv("SUPABASE_URL")
ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# 1. Login
r = requests.post(
    f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
    headers={"apikey": ANON_KEY, "Content-Type": "application/json"},
    json={"email": "test@example.com", "password": "test1234"},
)
token = r.json()["access_token"]
print("✅ Logged in")

# 2. Upload a PDF
pdf_path = input("Path to a PDF: ").strip()
if not os.path.exists(pdf_path):
    print(f"❌ File not found: {pdf_path}")
    exit(1)

print(f"Uploading {pdf_path}...")
with open(pdf_path, "rb") as f:
    r = requests.post(
        "http://localhost:8000/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": (os.path.basename(pdf_path), f, "application/pdf")},
    )

print(f"Status: {r.status_code}")
print(f"Response: {r.json()}")
doc_id = r.json().get("doc_id")
print(f"\n📄 Doc ID: {doc_id}")
print(f"⏳ Watch uvicorn terminal for progress...\n")

# 3. Poll status
for i in range(60):
    time.sleep(10)
    r = requests.get(
        f"http://localhost:8000/documents/{doc_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    doc = r.json()
    status = doc.get("status")
    pages = doc.get("page_count", 0)
    print(f"[{i*10+10}s] status={status} pages={pages}")

    if status == "ready":
        print("\n✅ DOCUMENT READY")
        break
    if status == "failed":
        print(f"\n❌ FAILED: {doc.get('error_message')}")
        break