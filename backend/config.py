import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

# LLM
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")
RERANK_MODEL = os.getenv("RERANK_MODEL", "openai/gpt-oss-20b")
EMBED_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-small-en-v1.5")

# Storage
CHROMA_DIR = Path(os.getenv("CHROMA_DIR", "./chroma_db"))
DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
CHROMA_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# Retrieval config
IN_PAGE_CHUNK_WORDS = 220
IN_PAGE_OVERLAP_WORDS = 40
CROSS_PAGE_CHUNK_WORDS = 80
TOP_K_CHUNKS = 20
TOP_K_PAGES = 5
TOP_K_SUMMARIES = 3
N_CLUSTERS = 12