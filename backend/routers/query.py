from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from db.auth import get_current_user
from db.supabase_client import get_service_client
from generation.answer import answer_stream

router = APIRouter(prefix="/query", tags=["query"])


class AskRequest(BaseModel):
    doc_id: str
    question: str


@router.post("/ask")
async def ask(
    req: AskRequest,
    user_id: str = Depends(get_current_user),
):
    # Verify document ownership
    service = get_service_client()
    result = service.table("documents").select("id, status").eq("id", req.doc_id).eq("user_id", user_id).execute()
    if not result.data:
        raise HTTPException(404, "Document not found")
    if result.data[0]["status"] != "ready":
        raise HTTPException(400, f"Document not ready (status: {result.data[0]['status']})")

    # Stream the answer as Server-Sent Events (SSE)
    def event_stream():
        try:
            for event in answer_stream(req.doc_id, req.question):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )