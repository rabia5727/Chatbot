"""
App entry point.

This file owns:
  1. Page config + global CSS
  2. Session-state initialisation
  3. Routing between the 4 screens based on st.session_state.page

Run with:  python -m streamlit run app.py
"""

import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="AI Assistant",
    page_icon="✨",
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
