"""
Face-recognition sign-up/login.

Owner: Rabia

How it fits together:
- register_face(user_id, image_bytes): call once, right after a normal
  sign_up + sign_in (db/auth.py), to save the user's face encoding.
  Runs on the normal session-scoped client, so RLS makes sure users can
  only write their own row.
- verify_face(image_bytes): the login-time counterpart. It has to check
  the new photo against EVERY stored encoding to figure out who it is —
  impossible while restricted to one user's own RLS-scoped rows — so
  this is the one function in the whole app that uses a second,
  privileged Supabase client (service_role key, SUPABASE_SERVICE_KEY in
  .env). That key must never reach a browser or get committed; it only
  ever runs here, server-side.
  Once it finds a match, it uses the Admin API to mint a real Supabase
  session for that user via a magic-link token — never touching their
  password — so the rest of the app (chat history, RLS) works exactly
  like a normal login afterward.

Integration contract:
- Both functions return/raise the same way as db/auth.py: plain
  dicts/None, ValueError with a readable message on failure.
- verify_face returns {"id", "email", "access_token", "refresh_token"} —
  same shape as db.auth.sign_in — so ui/sidebar.py can store it in
  st.session_state["user"] the same way either method returns.

Setup:
- pip install -r requirements.txt (face_recognition wraps dlib — see
  the Windows note in requirements.txt if it fails to build).
- Run the face_encodings table from db/schema.sql in the Supabase SQL
  editor.
- Add SUPABASE_SERVICE_KEY to .env — Supabase dashboard -> Project
  Settings -> API -> service_role key ("secret", not "publishable").
"""

import io

import face_recognition
import numpy as np
from supabase import create_client

from config.settings import get_settings
from db.supabase_client import supabase

MATCH_TOLERANCE = 0.6  # lower = stricter match. 0.6 is face_recognition's own default.

_admin_client = None


def _admin():
    """Lazily create the privileged (service_role) client — used only in this file."""
    global _admin_client
    if _admin_client is None:
        settings = get_settings()
        if not settings.supabase_service_key:
            raise ValueError("SUPABASE_SERVICE_KEY is not set in .env")
        _admin_client = create_client(settings.supabase_url, settings.supabase_service_key)
    return _admin_client


def _encode_face(image_bytes: bytes) -> list:
    """Return the 128-number encoding for the single face in `image_bytes`."""
    image = face_recognition.load_image_file(io.BytesIO(image_bytes))
    encodings = face_recognition.face_encodings(image)
    if len(encodings) == 0:
        raise ValueError("No face detected in the photo — try again with better lighting.")
    if len(encodings) > 1:
        raise ValueError("More than one face detected — make sure only you are in frame.")
    return encodings[0].tolist()


def register_face(user_id: str, image_bytes: bytes) -> None:
    """
    Save `user_id`'s face encoding. Call this while the user is already
    signed in (right after sign_up/sign_in) so RLS scopes the write to
    their own row.
    """
    encoding = _encode_face(image_bytes)
    try:
        supabase.table("face_encodings").upsert(
            {"user_id": user_id, "encoding": encoding}
        ).execute()
    except Exception as e:
        raise ValueError(f"Couldn't save face: {e}") from e


def verify_face(image_bytes: bytes) -> dict | None:
    """
    Identify who `image_bytes` belongs to by comparing against every
    registered face, and log them in for real if there's a match.

    Returns {"id", "email", "access_token", "refresh_token"}, or None
    if no registered face is a close enough match.
    """
    probe_encoding = np.array(_encode_face(image_bytes))

    try:
        rows = (
            _admin()
            .table("face_encodings")
            .select("user_id, encoding")
            .execute()
            .data
            or []
        )
    except Exception as e:
        raise ValueError(f"Couldn't look up registered faces: {e}") from e

    if not rows:
        return None

    known_encodings = [np.array(row["encoding"]) for row in rows]
    distances = face_recognition.face_distance(known_encodings, probe_encoding)
    best_index = int(np.argmin(distances))

    if distances[best_index] > MATCH_TOLERANCE:
        return None

    matched_user_id = rows[best_index]["user_id"]

    try:
        admin_user = _admin().auth.admin.get_user_by_id(matched_user_id)
        email = admin_user.user.email

        link_response = _admin().auth.admin.generate_link(
            {"type": "magiclink", "email": email}
        )
        token_hash = link_response.properties.hashed_token

        session_response = supabase.auth.verify_otp(
            {"type": "magiclink", "token_hash": token_hash}
        )
    except Exception as e:
        raise ValueError(f"Face matched but sign-in failed: {e}") from e

    return {
        "id": matched_user_id,
        "email": email,
        "access_token": session_response.session.access_token,
        "refresh_token": session_response.session.refresh_token,
    }
