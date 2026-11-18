import requests
import os
import json
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

# 2. Get latest document
r = requests.get(
    "http://localhost:8000/documents/",
    headers={"Authorization": f"Bearer {token}"},
)
docs = r.json()
if not docs:
    print("❌ No documents. Run test_upload.py first.")
    exit(1)

doc_id = docs[0]["id"]
print(f"📄 Using doc: {doc_id} ({docs[0]['name']})")

# 3. Ask a question (streamed)
question = input("\nQuestion: ").strip()
if not question:
    question = "What is this document about?"

print(f"\n🤖 Asking: {question}\n")
print("=" * 60)

r = requests.post(
    "http://localhost:8000/query/ask",
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    json={"doc_id": doc_id, "question": question},
    stream=True,
    timeout=120,
)

for line in r.iter_lines():
    if not line.startswith(b"data: "):
        continue
    data = json.loads(line[6:])

    if data["type"] == "token":
        print(data["content"], end="", flush=True)
    elif data["type"] == "done":
        print("\n" + "=" * 60)
        print(f"\n📚 Top pages: {data['top_pages']}")
        print(f"🔍 Candidates: {data['num_candidates']}")
    elif data["type"] == "error":
        print(f"\n❌ Error: {data['message']}")