"""Document metadata persistence, backed by Supabase (the `documents`
table from db/schema.sql).

Owner: Rabia (storage) / Ghanwa (async contract — rag/rag_service.py is
the only caller)

Note: RLS on `documents` restricts each user to their own rows — these
calls only succeed for an authenticated session (see db/auth.py).
"""

from __future__ import annotations

import asyncio
from typing import Any

from db.supabase_client import supabase


def _create_sync(metadata: dict[str, Any]) -> None:
    supabase.table("documents").insert(
        {
            "document_id": metadata["document_id"],
            "user_id": metadata["user_id"],
            "filename": metadata["filename"],
            "mime_type": metadata["mime_type"],
            "chunk_count": metadata["chunk_count"],
        }
    ).execute()


def _list_sync(user_id: str) -> list[dict[str, Any]]:
    response = (
        supabase.table("documents")
        .select("document_id, filename, mime_type, uploaded_at, chunk_count")
        .eq("user_id", user_id)
        .order("uploaded_at", desc=True)
        .execute()
    )
    return response.data or []


def _get_sync(document_id: str) -> dict[str, Any] | None:
    response = (
        supabase.table("documents").select("*").eq("document_id", document_id).limit(1).execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def _delete_sync(document_id: str, user_id: str) -> bool:
    owner = (
        supabase.table("documents")
        .select("document_id")
        .eq("document_id", document_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    if not owner.data:
        return False
    # Deleted explicitly (not left to ON DELETE CASCADE) to match Ghanwa's
    # original two-step delete and keep this testable without a real DB.
    supabase.table("chunks").delete().eq("document_id", document_id).execute()
    supabase.table("documents").delete().eq("document_id", document_id).execute()
    return True


async def create_document(metadata: dict[str, Any]) -> None:
    await asyncio.to_thread(_create_sync, metadata)


async def list_documents(user_id: str) -> list[dict[str, Any]]:
    return await asyncio.to_thread(_list_sync, user_id)


async def get_document(document_id: str) -> dict[str, Any] | None:
    return await asyncio.to_thread(_get_sync, document_id)


async def delete_document(document_id: str, user_id: str) -> bool:
    return await asyncio.to_thread(_delete_sync, document_id, user_id)
