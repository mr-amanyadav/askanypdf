import sys
import pickle
import re
import numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import (DATA_DIR, TOP_K_PAGES, TOP_K_SUMMARIES,
                    GROQ_API_KEY, RERANK_MODEL)
from indexing.in_page import search_chunks, get_model

_groq = None


def _llm():
    global _groq
    if _groq is None:
        from groq import Groq
        _groq = Groq(api_key=GROQ_API_KEY)
    return _groq


def _rerank(question: str, page_chunks: dict) -> list:
    """Batched re-rank on gpt-oss-20b. Returns top-K page numbers."""
    if not page_chunks:
        return []

    entries = []
    for p, chunks in page_chunks.items():
        excerpt = " ".join(chunks)[:400].replace("\n", " ")
        entries.append(f"{p}: {excerpt}")

    prompt = f"""Score how relevant each page is to answering the question, 0.0-1.0.

QUESTION: {question}

PAGES:
{chr(10).join(entries)}

Output ONLY lines of format "PAGENUM: SCORE". No prose.
Example:
12: 0.9
36: 0.3

Scores:"""

    try:
        resp = _llm().chat.completions.create(
            model=RERANK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=400,
        )
        text = (resp.choices[0].message.content or "").strip()
        scores = {}
        for m in re.finditer(r"(\d+)\s*:\s*([0-9]*\.?[0-9]+)", text):
            p = int(m.group(1))
            s = float(m.group(2))
            if p in page_chunks and 0 <= s <= 1:
                scores[p] = s

        if len(scores) < len(page_chunks) * 0.7:
            return list(page_chunks.keys())[:TOP_K_PAGES]

        return [p for p, _ in sorted(scores.items(), key=lambda x: -x[1])[:TOP_K_PAGES]]

    except Exception as e:
        print(f"[rerank] failed: {e}", flush=True)
        return list(page_chunks.keys())[:TOP_K_PAGES]


def _search_summaries(doc_id: str, query: str, top_k: int):
    path = DATA_DIR / f"{doc_id}_summaries.pkl"
    if not path.exists():
        return []

    with open(path, "rb") as f:
        data = pickle.load(f)

    model = get_model()
    q_emb = model.encode(query, convert_to_numpy=True)
    sims = np.dot(data["embeddings"], q_emb) / (
        np.linalg.norm(data["embeddings"], axis=1) * np.linalg.norm(q_emb) + 1e-9
    )
    top_idx = np.argsort(sims)[-top_k:][::-1]
    return [
        {**data["summaries"][i], "similarity": float(sims[i])}
        for i in top_idx
    ]


def retrieve_context(doc_id: str, question: str) -> dict:
    """Full retrieval: chunks → parent pages → re-rank + summary lookup."""
    # 1. Chunk retrieval
    chunk_hits = search_chunks(doc_id, question, top_k=20)

    page_chunks = {}
    for chunk, meta in chunk_hits:
        page_chunks.setdefault(meta["page"], []).append(chunk)

    # 2. Re-rank pages
    top_pages = _rerank(question, page_chunks)

    # 3. Summary retrieval
    summaries = _search_summaries(doc_id, question, top_k=TOP_K_SUMMARIES)

    # 4. Assemble context
    page_text = "\n\n".join(
        f"--- Page {p} ---\n" + "\n".join(page_chunks[p])[:800]
        for p in top_pages
    )

    summary_text = "\n\n".join(
        f"[pages {s['pages'][0]}-{s['pages'][-1]}]: {s['summary'][:300]}"
        for s in summaries
    )

    return {
        "top_pages": top_pages,
        "page_text": page_text,
        "summary_text": summary_text,
        "num_candidates": len(page_chunks),
    }