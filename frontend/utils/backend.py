"""
Real backend adapter for the frontend pages.

Replaces frontend.utils.mock_api — same function names/shapes so
pages/*.py needed only an import change, but every call here goes to
the real db/core/rag modules (Supabase + Gemini) instead of canned data.
"""

from __future__ import annotations

import asyncio

import streamlit as st

from core.chat_engine import send_message as _send_message
from db import auth as db_auth
from db import face_auth as db_face_auth
from db.supabase_client import supabase
from rag.rag_service import ingest_document as _ingest_document
from rag.rag_service import query_documents as _query_documents


def _sync_session() -> None:
    """Re-establish the signed-in user's Supabase session on the shared
    client before any RLS-protected call. Needed because `supabase` is one
    process-wide client and Streamlit reruns the whole script on every
    interaction -- nothing "remembers" who's logged in otherwise."""
    user = st.session_state.get("user") or {}
    access_token = user.get("access_token")
    refresh_token = user.get("refresh_token")
    if access_token and refresh_token:
        supabase.auth.set_session(access_token, refresh_token)


def _display_name(user_dict: dict) -> str:
    full_name = user_dict.get("full_name")
    if full_name:
        return full_name
    email = user_dict.get("email", "")
    return email.split("@")[0].replace(".", " ").title() or "User"


def _to_frontend_user(result: dict) -> dict:
    return {
        "id": result["id"],
        "name": _display_name(result),
        "email": result["email"],
        "access_token": result.get("access_token"),
        "refresh_token": result.get("refresh_token"),
    }


def signup_user(full_name: str, email: str, password: str, face_image_bytes=None) -> dict:
    """Create a real account. Face enrollment (if a photo was captured)
    happens right after, while the new session is active."""
    if not full_name or not email or not password:
        return {"success": False, "message": "Please fill in all required fields."}

    try:
        result = db_auth.sign_up(email, password, full_name=full_name)
    except ValueError as e:
        return {"success": False, "message": str(e)}

    if not result.get("access_token"):
        # "Confirm email" is on in the Supabase project -- no session yet,
        # so we can't register a face right now (register_face needs an
        # authenticated session for RLS). Stash it and finish the job the
        # first time this person actually logs in -- see login_user().
        if face_image_bytes:
            st.session_state.pending_face_bytes = face_image_bytes
            st.session_state.pending_face_user_id = result["id"]
        return {
            "success": True,
            "message": "Account created. Check your email to confirm it, then log in.",
        }

    if face_image_bytes:
        _sync_session()
        try:
            db_face_auth.register_face(result["id"], face_image_bytes)
        except ValueError as e:
            return {"success": True, "message": f"Account created, but face enrollment failed: {e}"}
        return {"success": True, "message": "Account created successfully. Face profile saved."}

    return {"success": True, "message": "Account created successfully. You can now log in."}


def enroll_face(image_bytes) -> dict:
    """Local-only capture acknowledgment. The real enrollment happens in
    signup_user() once the account (and its user_id) actually exists."""
    if image_bytes is None:
        return {"success": False, "message": "No face image captured."}
    return {"success": True, "message": "Face captured ✓ (saved when you create your account)"}


def login_user(email: str, password: str) -> dict:
    if not email or not password:
        return {"success": False, "message": "Please enter your email and password."}
    try:
        result = db_auth.sign_in(email, password)
    except ValueError as e:
        return {"success": False, "message": str(e)}

    message = "Logged in successfully."
    pending_bytes = st.session_state.pop("pending_face_bytes", None)
    pending_user_id = st.session_state.pop("pending_face_user_id", None)
    if pending_bytes and pending_user_id == result["id"]:
        # st.session_state["user"] isn't set yet at this point in the flow
        # (that happens after this function returns) -- _sync_session()
        # would find nothing, so set the session directly from this
        # sign_in's own tokens instead.
        if result.get("access_token") and result.get("refresh_token"):
            supabase.auth.set_session(result["access_token"], result["refresh_token"])
        try:
            db_face_auth.register_face(result["id"], pending_bytes)
            message = "Logged in successfully. Face profile saved."
        except ValueError:
            pass  # login still succeeded; they can just skip face login

    return {"success": True, "message": message, "user": _to_frontend_user(result)}


def verify_face(image_bytes) -> dict:
    if image_bytes is None:
        return {"success": False, "message": "No face image captured.", "user": None}
    try:
        result = db_face_auth.verify_face(image_bytes)
    except ValueError as e:
        return {"success": False, "message": str(e), "user": None}
    if result is None:
        return {"success": False, "message": "Face not recognized.", "user": None}
    return {"success": True, "message": "Face verified ✓", "user": _to_frontend_user(result)}


def send_chat_message(message: str, uploaded_file=None) -> dict:
    user = st.session_state.get("user") or {}
    user_id = user.get("id", "anonymous")
    _sync_session()

    if uploaded_file is not None:
        try:
            file_bytes = uploaded_file.getvalue()
            mime_type = uploaded_file.type or "application/octet-stream"
            ingested = asyncio.run(
                _ingest_document(user_id, uploaded_file.name, mime_type, file_bytes)
            )
            result = asyncio.run(
                _query_documents(user_id, message, document_id=ingested["document_id"])
            )
            return {"type": "rag", "source": uploaded_file.name, "answer": result["answer"]}
        except Exception as e:
            return {"type": "normal", "answer": f"Sorry, I couldn't process that document: {e}"}

    try:
        answer = asyncio.run(_send_message(user_id, message))
        return {"type": "normal", "answer": answer}
    except Exception as e:
        return {"type": "normal", "answer": f"Sorry, something went wrong: {e}"}


def upload_document(file) -> dict:
    """Capture acknowledgment only -- the real ingestion happens inside
    send_chat_message() once there's a question to answer about it."""
    if file is None:
        return {"success": False, "filename": None}
    return {"success": True, "filename": file.name}
