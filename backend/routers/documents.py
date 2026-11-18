from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from db.auth import get_current_user
from db.supabase_client import get_service_client
import uuid

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload")
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files allowed")

    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(400, "File too large (max 50 MB)")

    doc_id = str(uuid.uuid4())
    storage_path = f"{user_id}/{doc_id}.pdf"

    service = get_service_client()

    try:
        service.storage.from_("pdfs").upload(
            storage_path,
            content,
            {"content-type": "application/pdf"},
        )
    except Exception as e:
        raise HTTPException(500, f"Storage upload failed: {e}")

    try:
        service.table("documents").insert({
            "id": doc_id,
            "user_id": user_id,
            "name": file.filename.rsplit(".", 1)[0],
            "filename": file.filename,
            "storage_path": storage_path,
            "status": "pending",
        }).execute()
    except Exception as e:
        raise HTTPException(500, f"DB insert failed: {e}")

    from ingestion.pipeline import run_ingestion_pipeline
    background_tasks.add_task(run_ingestion_pipeline, doc_id, storage_path, user_id)

    return {"doc_id": doc_id, "status": "pending", "filename": file.filename}


@router.get("/")
async def list_documents(user_id: str = Depends(get_current_user)):
    service = get_service_client()
    result = service.table("documents").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    return result.data


@router.get("/{doc_id}")
async def get_document(doc_id: str, user_id: str = Depends(get_current_user)):
    service = get_service_client()
    result = service.table("documents").select("*").eq("id", doc_id).eq("user_id", user_id).execute()
    if not result.data:
        raise HTTPException(404, "Document not found")
    return result.data[0]


@router.delete("/{doc_id}")
async def delete_document(doc_id: str, user_id: str = Depends(get_current_user)):
    service = get_service_client()
    result = service.table("documents").select("storage_path").eq("id", doc_id).eq("user_id", user_id).execute()
    if not result.data:
        raise HTTPException(404, "Document not found")

    try:
        service.storage.from_("pdfs").remove([result.data[0]["storage_path"]])
    except Exception:
        pass

    service.table("documents").delete().eq("id", doc_id).eq("user_id", user_id).execute()
    return {"deleted": True}