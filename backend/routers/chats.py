from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from db.auth import get_current_user
from db.supabase_client import get_service_client
import uuid

router = APIRouter(prefix="/chats", tags=["chats"])


class SaveMessageRequest(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    citations: dict | None = None
    metadata: dict | None = None


def _get_or_create_chat(service, user_id: str, doc_id: str) -> dict:
    """Find existing chat for (user, doc) or create a new one."""
    existing = (
        service.table("chats")
        .select("*")
        .eq("user_id", user_id)
        .eq("document_id", doc_id)
        .execute()
    )
    if existing.data:
        return existing.data[0]

    # Create new chat
    new_chat = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "document_id": doc_id,
        "title": "New chat",
    }
    result = service.table("chats").insert(new_chat).execute()
    return result.data[0]


@router.get("/{doc_id}")
async def get_chat_for_document(
    doc_id: str,
    user_id: str = Depends(get_current_user),
):
    """Get (or create) the chat for this document."""
    service = get_service_client()

    # Verify document ownership
    doc = service.table("documents").select("id").eq("id", doc_id).eq("user_id", user_id).execute()
    if not doc.data:
        raise HTTPException(404, "Document not found")

    chat = _get_or_create_chat(service, user_id, doc_id)
    return chat


@router.get("/{doc_id}/messages")
async def list_messages(
    doc_id: str,
    user_id: str = Depends(get_current_user),
):
    """List all messages in this document's chat, oldest first."""
    service = get_service_client()

    # Verify document ownership
    doc = service.table("documents").select("id").eq("id", doc_id).eq("user_id", user_id).execute()
    if not doc.data:
        raise HTTPException(404, "Document not found")

    # Get (or create) chat
    chat = _get_or_create_chat(service, user_id, doc_id)

    # Fetch messages
    result = (
        service.table("messages")
        .select("*")
        .eq("chat_id", chat["id"])
        .order("created_at", desc=False)
        .execute()
    )
    return result.data


@router.post("/{doc_id}/messages")
async def save_message(
    doc_id: str,
    body: SaveMessageRequest,
    user_id: str = Depends(get_current_user),
):
    """Save a message (user or assistant) to this document's chat."""
    service = get_service_client()

    # Verify document ownership
    doc = service.table("documents").select("id").eq("id", doc_id).eq("user_id", user_id).execute()
    if not doc.data:
        raise HTTPException(404, "Document not found")

    chat = _get_or_create_chat(service, user_id, doc_id)

    msg = {
        "id": str(uuid.uuid4()),
        "chat_id": chat["id"],
        "role": body.role,
        "content": body.content,
        "citations": body.citations,
        "metadata": body.metadata,
    }
    result = service.table("messages").insert(msg).execute()
    return result.data[0]