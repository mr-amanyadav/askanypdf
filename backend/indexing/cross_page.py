import numpy as np
import pickle
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import (DATA_DIR, CROSS_PAGE_CHUNK_WORDS, N_CLUSTERS,
                    GROQ_API_KEY, LLM_MODEL)
from indexing.in_page import get_model, chunk_text

_groq = None


def get_llm():
    global _groq
    if _groq is None:
        from groq import Groq
        _groq = Groq(api_key=GROQ_API_KEY)
    return _groq


def _summarize(cluster_text: str, pages: list) -> str:
    prompt = f"""Summarize these excerpts from pages {pages} of a document. 2-3 sentences. Include key facts and numbers.

{cluster_text[:3500]}

Summary:"""
    try:
        resp = get_llm().chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=250,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        return f"[Summary unavailable: {e}]"


def build_cross_page_tree(doc_id: str, parsed: dict) -> list:
    all_chunks = []
    for page in parsed["pages"]:
        for c in chunk_text(page["text"], CROSS_PAGE_CHUNK_WORDS, 0):
            all_chunks.append({"text": c, "page": page["page"]})

    if len(all_chunks) < N_CLUSTERS:
        print(f"[cross_page] too few chunks ({len(all_chunks)}) — skipping", flush=True)
        return []

    model = get_model()
    print(f"[cross_page] Embedding {len(all_chunks)} chunks for clustering...", flush=True)
    embs = model.encode(
        [c["text"] for c in all_chunks],
        batch_size=32,
        show_progress_bar=True,
        convert_to_numpy=True,
    )

    from sklearn.mixture import GaussianMixture
    gmm = GaussianMixture(n_components=N_CLUSTERS, random_state=42, n_init=3)
    labels = gmm.fit_predict(embs)

    print(f"[cross_page] Summarizing {N_CLUSTERS} clusters (LLM calls)...", flush=True)
    summaries = []
    for k in range(N_CLUSTERS):
        cluster_chunks = [all_chunks[i] for i in range(len(all_chunks)) if labels[i] == k]
        if not cluster_chunks:
            continue
        pages = sorted(set(c["page"] for c in cluster_chunks))
        text = "\n\n".join(c["text"][:400] for c in cluster_chunks[:40])
        summary = _summarize(text, pages)
        summaries.append({
            "summary": summary,
            "pages": pages,
            "chunk_count": len(cluster_chunks),
        })
        print(f"[cross_page]   cluster {k+1}/{N_CLUSTERS} → {len(pages)} pages", flush=True)

    summary_embs = model.encode([s["summary"] for s in summaries], convert_to_numpy=True)
    out_path = DATA_DIR / f"{doc_id}_summaries.pkl"
    with open(out_path, "wb") as f:
        pickle.dump({"summaries": summaries, "embeddings": summary_embs}, f)

    print(f"[cross_page] ✅ {len(summaries)} summaries saved", flush=True)
    return summaries