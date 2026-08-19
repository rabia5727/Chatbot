"""
User auth via Supabase (email/password to start — extend if needed).

Owner: Rabia

Integration contract:
- sign_up / sign_in / sign_out / get_current_user are the only functions
  ui/sidebar.py calls. Return simple dicts/None, not raw Supabase
  response objects, so the UI layer doesn't need to know Supabase's
  response shape.
"""

from db.supabase_client import supabase


def sign_up(email: str, password: str) -> dict:
    """TODO(Rabia): supabase.auth.sign_up(...), return {"id", "email"} or raise."""
    raise NotImplementedError("Rabia: implement sign up")


def sign_in(email: str, password: str) -> dict:
    """TODO(Rabia): supabase.auth.sign_in_with_password(...)."""
    raise NotImplementedError("Rabia: implement sign in")


def sign_out() -> None:
    """TODO(Rabia): supabase.auth.sign_out()."""
    raise NotImplementedError("Rabia: implement sign out")


def get_current_user() -> dict | None:
    """TODO(Rabia): return the currently signed-in user, or None."""
    raise NotImplementedError("Rabia: implement current-user lookup")
