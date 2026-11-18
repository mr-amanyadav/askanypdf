import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from db.supabase_client import get_service_client
from ingestion.pdf_parser import parse_pdf
from indexing.in_page import build_index
from indexing.cross_page import build_cross_page_tree
from config import DATA_DIR


async def run_ingestion_pipeline(doc_id: str, storage_path: str, user_id: str):
    """Download → parse → index → summarize. Updates DB status at each stage."""
    service = get_service_client()

    def _update(status, **extra):
        service.table("documents").update({"status": status, **extra}).eq("id", doc_id).execute()

    try:
        _update("indexing")

        print(f"[pipeline] Downloading {storage_path}...", flush=True)
        tmp_pdf = DATA_DIR / f"{doc_id}.pdf"
        content = service.storage.from_("pdfs").download(storage_path)
        tmp_pdf.write_bytes(content)

        print(f"[pipeline] Parsing PDF...", flush=True)
        parsed = parse_pdf(tmp_pdf)
        page_count = len(parsed["pages"])
        _update("indexing", page_count=page_count)
        print(f"[pipeline] Parsed {page_count} pages", flush=True)

        print(f"[pipeline] Building in-page index...", flush=True)
        build_index(doc_id, parsed)

        print(f"[pipeline] Building cross-page tree...", flush=True)
        build_cross_page_tree(doc_id, parsed)

        tmp_pdf.unlink(missing_ok=True)
        _update("ready")
        print(f"[pipeline] ✅ Document {doc_id} ready", flush=True)

    except Exception as e:
        print(f"[pipeline] ❌ Failed: {e}", flush=True)
        _update("failed", error_message=str(e)[:500])
        raise