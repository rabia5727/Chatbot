"""
User auth via Supabase (email/password).

Owner: Rabia

Integration contract:
- sign_up / sign_in / sign_out / get_current_user / request_password_reset /
  update_password are the only functions ui/sidebar.py calls. They
  return plain dicts/None (never raw Supabase SDK objects) so the UI
  layer doesn't need to know Supabase's response shape, and raise
  ValueError with a readable message on failure.
- sign_up/sign_in return {"id", "email", "access_token", "refresh_token"}.
  The UI stores this dict in st.session_state["user"]. Because `supabase`
  (db/supabase_client.py) is a single client shared by the whole running
  app, we never rely on it "remembering" who's logged in — every call
  that needs a session re-sets it from the tokens passed in.
- Forgot-password is two steps: request_password_reset(email) sends the
  reset email; update_password(access_token, refresh_token, new_password)
  sets the new password using the tokens from the link in that email
  (Supabase appends them to the redirect URL — the UI has to read them
  out of it, e.g. via st.query_params).
"""

from db.supabase_client import supabase


def _to_user_dict(auth_response) -> dict:
    user = auth_response.user
    session = auth_response.session
    return {
        "id": user.id,
        "email": user.email,
        "access_token": session.access_token if session else None,
        "refresh_token": session.refresh_token if session else None,
    }


def sign_up(email: str, password: str) -> dict:
    """Create a new account, return {"id", "email", "access_token", "refresh_token"}."""
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
    except Exception as e:
        raise ValueError(f"Sign up failed: {e}") from e
    if response.user is None:
        raise ValueError("Sign up failed — check the email/password and try again.")
    return _to_user_dict(response)


def sign_in(email: str, password: str) -> dict:
    """Log in an existing user, return {"id", "email", "access_token", "refresh_token"}."""
    try:
        response = supabase.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
    except Exception as e:
        raise ValueError("Incorrect email or password.") from e
    return _to_user_dict(response)


def sign_out() -> None:
    """Sign the current session out. Safe to call even if already signed out."""
    try:
        supabase.auth.sign_out()
    except Exception:
        pass


def get_current_user(access_token: str, refresh_token: str) -> dict | None:
    """
    Restore a session from stored tokens (e.g. after a Streamlit rerun)
    and return {"id", "email"}, or None if the tokens are missing/expired.
    """
    if not access_token or not refresh_token:
        return None
    try:
        supabase.auth.set_session(access_token, refresh_token)
        response = supabase.auth.get_user()
    except Exception:
        return None
    if response is None or response.user is None:
        return None
    return {"id": response.user.id, "email": response.user.email}


def request_password_reset(email: str) -> None:
    """
    Send a password-reset email to `email` via Supabase Auth. Always
    "succeeds" from the caller's point of view (matches Supabase's own
    behavior of not revealing whether an email is registered) unless the
    request itself fails, e.g. a network error.

    Requires a Redirect URL to be whitelisted in the Supabase dashboard
    (Authentication -> URL Configuration) — that's where the reset link
    in the email sends the user, with the tokens update_password() needs
    attached as URL params.
    """
    try:
        supabase.auth.reset_password_for_email(email)
    except Exception as e:
        raise ValueError(f"Couldn't send reset email: {e}") from e


def update_password(access_token: str, refresh_token: str, new_password: str) -> None:
    """
    Set a new password using the tokens from the reset-link URL (see
    request_password_reset). Raises ValueError if the tokens are
    missing/expired or the update otherwise fails.
    """
    try:
        supabase.auth.set_session(access_token, refresh_token)
        supabase.auth.update_user({"password": new_password})
    except Exception as e:
        raise ValueError(f"Couldn't update password: {e}") from e
