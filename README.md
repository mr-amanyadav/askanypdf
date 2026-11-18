# AskAnyPDF

> Chat with any PDF using AI. Upload a document, ask questions, get answers with page citations — streamed word-by-word.

A full-stack RAG (Retrieval-Augmented Generation) application implementing the **MHier-RAG** architecture for multimodal long-context document question-answering.

---

## ✨ Features

- 📄 Upload any PDF (up to 50 MB)
- 🚀 Fast indexing (13 pages in ~40 sec, 169 pages in ~4 min)
- 💬 Streaming answers (word-by-word)
- 📚 Page citations on every answer
- 🔐 Multi-user auth via Supabase
- 🗑️ Delete documents and switch chats
- 📊 Visual progress bars during indexing
- 🎨 ChatGPT-like UI with dark sidebar

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│  BROWSER (React + Vite + Tailwind)                      │
│  Login · Upload · Chat · Sidebar                        │
└──────┬──────────────────────────────────────────────────┘
       │ (JWT auth)
       ▼
┌─────────────────────────────────────────────────────────┐
│  SUPABASE (Mumbai · ap-south-1)                         │
│  Auth · Postgres (RLS) · Storage (per-user folders)     │
└──────┬──────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  FASTAPI BACKEND                                        │
│                                                         │
│  INGESTION (background, 30-240 sec)                     │
│   1. Download PDF → PyMuPDF parse (text + tables)       │
│   2. Chunk into 220-word segments                       │
│   3. Embed with bge-small-en-v1.5 → ChromaDB            │
│   4. GMM cluster (12 clusters)                          │
│   5. LLM summaries per cluster (gpt-oss-120b)           │
│                                                         │
│  QUERY (per question, ~3-5 sec)                         │
│   1. Embed question → retrieve top-20 chunks            │
│   2. Group by page → batched LLM re-rank (gpt-oss-20b)  │
│   3. Retrieve top-3 cross-page summaries                │
│   4. CoT prompt → stream answer (gpt-oss-120b) via SSE  │
└──────┬──────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  GROQ API (free tier)                                   │
│  gpt-oss-120b (answers) · gpt-oss-20b (re-ranking)      │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start (Local Development)

### Prerequisites

- Python 3.11+ — https://www.python.org/downloads/
- Node.js 20+ — https://nodejs.org
- Git — https://git-scm.com

### Free Accounts

- Supabase — https://supabase.com (database + auth)
- Groq — https://console.groq.com (LLM API)

### Step 1: Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/AskAnyPDF.git
cd AskAnyPDF
```

### Step 2: Backend setup

```bash
cd backend
python -m venv venv
```

Activate the virtual environment:

```powershell
# Windows
venv\Scripts\activate
```

```bash
# Mac/Linux
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create `.env` file:

```bash
cp .env.example .env
```

Edit `backend/.env` with your credentials:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
SUPABASE_JWT_SECRET=your-jwt-secret

GROQ_API_KEY=gsk_your-groq-key

LLM_MODEL=openai/gpt-oss-120b
RERANK_MODEL=openai/gpt-oss-20b
EMBED_MODEL=BAAI/bge-small-en-v1.5

CHROMA_DIR=./chroma_db
DATA_DIR=./data
```

Start the backend:

```bash
uvicorn main:app --reload --port 8000
```

Verify it works:

```bash
curl http://localhost:8000/health
```

Expected: `{"status":"ok"}`

### Step 3: Supabase setup

In your Supabase dashboard:

1. Create project in **Mumbai (ap-south-1)** region
2. Run schema: paste `supabase/migrations/001_init.sql` into SQL Editor → Run
3. Create storage bucket: Storage → New bucket → name `pdfs` → Public: No
4. Apply storage policy: copy the policy SQL from `001_init.sql` → run in SQL Editor
5. Disable email confirmation: Auth → Providers → toggle off "Confirm email"
6. Create test user: Auth → Users → Add user → `test@example.com` / `test1234` (auto-confirm)

### Step 4: Frontend setup

```bash
cd frontend
npm install
cp .env.example .env
```

Edit `frontend/.env`:

```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_API_URL=http://localhost:8000
```

Note: `VITE_` prefix is required. Use anon key (not service key).

Start the frontend:

```bash
npm run dev
```

Expected: `VITE ready at http://localhost:5173`

### Step 5: Use the app

1. Open **http://localhost:5173**
2. Sign in with `test@example.com` / `test1234` (or sign up)
3. Upload a PDF with the "Upload PDF" button
4. Wait for indexing (~40 sec small, ~4 min large)
5. Click the document in the sidebar
6. Ask a question and watch it stream in

---

## 🧪 Testing with Sample PDF

Use the NVIDIA FY2023 10-K (169 pages) to test the full pipeline. Download from NVIDIA Investor Relations.

Verified sample questions:

| Question | Expected Answer | Page |
|----------|-----------------|------|
| How many full-time employees does NVIDIA have? | 26,196 | 12 |
| Total amortization expense for intangible assets in FY2023? | $699 million | 72 |
| Future purchase commitments for FY2024? | $5,230 million | 79 |

First query takes 30-60 sec (Supabase cold start). Subsequent queries: 3-5 sec.

---

## 📦 Tech Stack

### Backend

- FastAPI — modern Python API framework
- PyMuPDF — PDF text + table extraction
- ChromaDB — vector database (persistent)
- sentence-transformers — BAAI/bge-small-en-v1.5 embeddings
- scikit-learn — Gaussian Mixture Model clustering
- Groq SDK — OpenAI-compatible LLM API
- Supabase Python client — DB + auth + storage

### Frontend

- React 18 + TypeScript
- Vite — build tool
- Tailwind CSS v3 — utility-first styling
- Supabase JS — browser auth
- @microsoft/fetch-event-source — SSE client

### Infrastructure

- Supabase (Mumbai) — Postgres + Auth + Storage
- Groq — LLM inference (free tier)
- Render — backend hosting (planned)
- Vercel — frontend hosting (planned)

Total cost: $0/month (all free tiers)

---

## 📊 Performance

| Metric | Value |
|--------|-------|
| Indexing (13 pages) | ~40 sec |
| Indexing (169 pages) | ~4 min |
| Query latency (warm) | 3-5 sec |
| First query (cold start) | 30-60 sec |
| Embedding model size | 133 MB |
| ChromaDB size (169 pages) | ~50 MB |
| Answer accuracy (verified) | 4/4 correct |

---

## 🎓 Design Decisions

### 1. PDF Parsing: PyMuPDF (not Docling)

The paper uses Docling for richer extraction. We switched to PyMuPDF because:

- Docling's ML pipeline crashes on Windows (threading deadlock in `docling>=2.0`)
- PyMuPDF is 50x faster (2 sec vs 100 sec for a 169-page doc)
- Text + table extraction is sufficient for RAG

### 2. Two-Tier LLM Strategy

| Task | Model | Why |
|------|-------|-----|
| Re-ranking | gpt-oss-20b | Fast, structured JSON, 2 sec |
| Answer generation | gpt-oss-120b | Reasoning model, higher quality, 4 sec |
| Summaries | gpt-oss-120b | One-time cost per document |

Why not one model? gpt-oss-120b returns prose instead of structured format. gpt-oss-20b follows format but has lower reasoning.

### 3. Batched Re-ranking

The paper does 20 individual LLM calls. We do 1 batched call (all 20 pages in one prompt):

- 7x faster (2 sec vs 15 sec)
- ~95% of accuracy (relative comparison works well)
- Tested: page 79 (with $5,230M) ranked #7 by raw similarity, moved to #1 by batched re-ranker

### 4. Streaming via SSE

Answers stream word-by-word via Server-Sent Events:

- Perceived latency: ~1 sec (first token) vs 5 sec (full answer)
- Feels 5x faster despite same total time
- Standard pattern (OpenAI, Anthropic, ChatGPT all stream)

### 5. Optimistic UI + Reconciliation

Uploads and deletes update state instantly:

- Optimistic insert: doc appears in sidebar immediately
- After backend success: refresh from server
- On failure: roll back optimistic change
- Tombstone set: prevents stale polls from resurrecting deleted docs

### 6. Mumbai Region

Supabase project is in `ap-south-1` (Mumbai):

- Latency: 30ms (Mumbai) vs 250ms (US-East)
- Auth: 2 sec vs 43 sec cold start
- Query: 4 sec vs 15+ sec

---

## ⚠️ Known Limitations

### Not Implemented

- Image extraction — charts and figures are ignored (only text + tables)
- OCR for scanned PDFs — image-only PDFs return empty text
- Chat persistence — messages reset on page refresh
- Chat titles — all chats show "New chat"
- Multiple chats per doc — resets on switching documents
- Mobile optimization — desktop-first UI
- Markdown rendering — only `**bold**` supported
- PDF preview — no in-browser viewer
- Drag-and-drop upload — click-to-upload only
- Rate limiting per user — Groq global limits only
- User settings — email/password change requires Supabase dashboard
- Tests — no pytest, no Playwright

### Technical Constraints

- Free-tier cold starts: Supabase sleeps after 15 min idle → 30-60 sec first request
- Groq limits: 14,400 requests/day, 8K tokens/min
- PDFs > 100 pages: indexing takes 4+ minutes on CPU
- No GPU: all embeddings on CPU (~10x slower than paper's A100)
- Re-ranker non-determinism: gpt-oss-20b occasionally fails to parse (~10% of runs), falls back to raw chunk order
- Single-level clustering: paper uses multi-level tree; we use 15 clusters (single level)
- No cross-user caching: same PDF uploaded by 2 users is indexed twice
- Full re-index required: delete + re-upload to refresh
- ChromaDB on disk: not a managed vector DB

---

## 📚 Project Structure

```
AskAnyPDF/
├── README.md
├── .gitignore
│
├── backend/
│   ├── requirements.txt
│   ├── .env.example
│   ├── main.py
│   ├── config.py
│   ├── db/
│   │   ├── auth.py
│   │   └── supabase_client.py
│   ├── routers/
│   │   ├── documents.py
│   │   └── query.py
│   ├── ingestion/
│   │   ├── pdf_parser.py
│   │   └── pipeline.py
│   ├── indexing/
│   │   ├── in_page.py
│   │   └── cross_page.py
│   ├── retrieval/
│   │   └── retriever.py
│   └── generation/
│       └── answer.py
│
├── frontend/
│   ├── package.json
│   ├── .env.example
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── index.css
│       ├── lib/
│       │   ├── supabase.ts
│       │   ├── api.ts
│       │   └── AuthContext.tsx
│       ├── pages/
│       │   └── Login.tsx
│       └── components/
│           ├── Sidebar.tsx
│           ├── ChatWindow.tsx
│           └── ProgressBar.tsx
│
├── supabase/
│   └── migrations/
│       └── 001_init.sql
│
└── scripts/
    ├── test_auth.py
    ├── test_upload.py
    └── test_query.py
```

---

## 🔐 Environment Variables

### Backend (`backend/.env`)

| Variable | Purpose |
|----------|---------|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_ANON_KEY` | Public anon key |
| `SUPABASE_SERVICE_KEY` | Service role key (secret) |
| `SUPABASE_JWT_SECRET` | JWT signing secret |
| `GROQ_API_KEY` | Groq API key |
| `LLM_MODEL` | openai/gpt-oss-120b |
| `RERANK_MODEL` | openai/gpt-oss-20b |
| `EMBED_MODEL` | BAAI/bge-small-en-v1.5 |
| `CHROMA_DIR` | ./chroma_db |
| `DATA_DIR` | ./data |

### Frontend (`frontend/.env`)

| Variable | Purpose |
|----------|---------|
| `VITE_SUPABASE_URL` | Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | Public anon key |
| `VITE_API_URL` | Backend URL |

Security notes:

- Never commit `.env` files
- Never put SERVICE_KEY in frontend
- `VITE_` prefix on frontend vars is required

---

## 🐛 Troubleshooting

### Backend won't start

`ModuleNotFoundError: No module named X` → run `pip install -r requirements.txt` with venv active

`Error: Invalid API key` → check `SUPABASE_SERVICE_KEY` is the service_role key, not anon

### Upload fails with 500

- Check uvicorn terminal for traceback
- Verify `pdfs` bucket exists in Supabase Storage
- Verify schema is applied

### Chat hangs / no streaming

- Check uvicorn for `POST /query/ask HTTP/1.1 200 OK`
- Check Groq rate limits at console.groq.com/usage
- First query after cold start takes 30-60 sec

### White page on frontend

- F12 → Console → paste error
- Common: `.env` missing or has placeholder values → restart `npm run dev`
- Check `VITE_` prefix on all vars

### Tailwind warnings in VS Code

`Unknown at rule @tailwind` → harmless. Add `.vscode/settings.json`: `{"css.lint.unknownAtRules": "ignore"}`

---

## 🎯 What This Project Demonstrates

For viva / job interviews:

1. Research paper implementation — MHier-RAG architecture replicated on real data
2. Full-stack engineering — React + FastAPI + Supabase + vector DB
3. RAG pipeline — chunking, embedding, clustering, retrieval, re-ranking, CoT generation
4. Streaming architecture — SSE, async generators, incremental UI
5. Production patterns — JWT auth, RLS, optimistic UI, error rollback
6. Real-world debugging — Docling crashes, JWKS migration, model deprecation, region latency
7. Cost consciousness — $0/month using only free tiers

Verified results: 4/4 correct answers on NVIDIA 10-K (26,196 employees, $699M amortization, $5,230M commitments, business overview) — the last one required the LLM re-ranker to promote page 79 from rank #7 to rank #1.

---

## 📚 Reference

This project implements:

> MHier-RAG: Hierarchical Retrieval-Augmented Generation for Multimodal Long-Context Document Question Answering

Key ideas from the paper:

- In-page flattened chunk index + cross-page topological cluster index
- Multi-granularity retrieval (page-level parent + document-level summary)
- LLM-based re-ranking for multi-modal evidence connection
- Chain-of-Thought answer generation with structured output

---

## 📄 License

MIT

---

## 🙏 Acknowledgments

- Original paper authors for the MHier-RAG architecture
- Artifex for PyMuPDF
- HuggingFace for sentence-transformers and BAAI models
- Groq for free-tier LLM API access
- Supabase for free-tier database + auth + storage
- Vercel + Render for free-tier deployment

---

## 📊 Stats

- ~3,500 lines of code
- ~2,200 lines Python (backend)
- ~1,100 lines TypeScript/TSX (frontend)
- ~200 lines SQL (schema)
- Built in: ~40 hours across 3 weeks
- Cost: $0/month (all free tiers)

---

Built as a course project demonstrating production-grade RAG system implementation from academic research.