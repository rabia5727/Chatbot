"""
App entry point.

This file owns:
  1. Page config + global CSS
  2. Session-state initialisation
  3. Routing between the 4 screens based on st.session_state.page

Run with:  python -m streamlit run app.py
"""

import sys
from pathlib import Path

import streamlit as st

# frontend/ is what Streamlit puts on sys.path (so `pages`/`components`/
# `utils` resolve), but utils/backend.py needs to reach the project's
# top-level core/db/rag/tools/config packages one directory up -- add the
# repo root too, before anything below imports backend.py.
#
# Appended, not inserted at 0: the repo root also has its own stale
# top-level `utils/` package (leftover from the original scaffold, now
# superseded by frontend/). Prepending it would let that shadow
# frontend/utils/ instead of the real one -- append so frontend/'s own
# packages are always found first, and the repo root is only consulted
# for names frontend/ doesn't have (core, db, rag, tools, config).
_REPO_ROOT = str(Path(__file__).resolve().parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.append(_REPO_ROOT)

st.set_page_config(
    page_title="AI Assistant",
    page_icon=":material/forum:",
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_css() -> None:
    css_path = Path(__file__).parent / "styles" / "main.css"
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css()

# ---------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = "signup"  # first screen in the required flow

if "user" not in st.session_state:
    st.session_state.user = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Hide sidebar on Auth screens so Sign Up, Login, and Face Login are clean
if st.session_state.page != "chatbot":
    st.markdown(
        "<style>section[data-testid='stSidebar'] { display: none !important; }</style>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------
from pages import signup, login, face_login, chatbot  # noqa: E402

ROUTES = {
    "signup": signup.render,
    "login": login.render,
    "face_login": face_login.render,
    "chatbot": chatbot.render,
}


def route() -> None:
    # Guard: only a logged-in user (via password or face) can reach chatbot.
    if st.session_state.page == "chatbot" and st.session_state.user is None:
        st.session_state.page = "login"

    render_fn = ROUTES.get(st.session_state.page, login.render)
    render_fn()


route()
