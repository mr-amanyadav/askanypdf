import chromadb
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import (CHROMA_DIR, EMBED_MODEL, IN_PAGE_CHUNK_WORDS,
                    IN_PAGE_OVERLAP_WORDS, TOP_K_CHUNKS)

_model = None


def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        print(f"[index] Loading embedding model: {EMBED_MODEL}", flush=True)
        _model = SentenceTransformer(EMBED_MODEL)
    return _model


def chunk_text(text: str, size: int, overlap: int) -> list:
    words = text.split()
    chunks, i = [], 0
    while i < len(words):
        chunk = " ".join(words[i:i + size])
        if chunk.strip():
            chunks.append(chunk)
        if i + size >= len(words):
            break
        i += size - overlap
    return chunks


def build_index(doc_id: str, parsed: dict) -> int:
    """Build in-page ChromaDB collection. Returns chunk count."""
    model = get_model()
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection_name = f"doc_{doc_id}"

    try:
        client.delete_collection(collection_name)
    except Exception:
        pass
    col = client.create_collection(collection_name, metadata={"hnsw:space": "cosine"})

    ids, docs, metadatas = [], [], []

    for page in parsed["pages"]:
        for chunk in chunk_text(page["text"], IN_PAGE_CHUNK_WORDS, IN_PAGE_OVERLAP_WORDS):
            ids.append(f"c{len(ids)}")
            docs.append(chunk)
            metadatas.append({"page": page["page"], "type": "text"})

        for t_idx, table in enumerate(page["tables"]):
            table_text = "\n".join(
                " | ".join(str(c) if c else "" for c in row)
                for row in table
            )
            if len(table_text) > 50:
                ids.append(f"c{len(ids)}")
                docs.append(f"[TABLE from page {page['page']}]\n{table_text}")
                metadatas.append({"page": page["page"], "type": "table"})

    if not docs:
        raise RuntimeError("No text or tables found in PDF")

    print(f"[index] Embedding {len(docs)} chunks...", flush=True)
    embeddings = model.encode(
        docs,
        batch_size=32,
        show_progress_bar=True,
        convert_to_numpy=True,
    ).tolist()

    for i in range(0, len(docs), 500):
        col.add(
            ids=ids[i:i + 500],
            documents=docs[i:i + 500],
            metadatas=metadatas[i:i + 500],
            embeddings=embeddings[i:i + 500],
        )

    print(f"[index] ✅ Indexed {len(docs)} chunks", flush=True)
    return len(docs)


def search_chunks(doc_id: str, query: str, top_k: int = TOP_K_CHUNKS):
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    col = client.get_collection(f"doc_{doc_id}")
    model = get_model()
    q_emb = model.encode(query, convert_to_numpy=True).tolist()
    results = col.query(query_embeddings=[q_emb], n_results=top_k)
    return list(zip(results["documents"][0], results["metadatas"][0]))