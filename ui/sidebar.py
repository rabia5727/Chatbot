"""
Sidebar: login/signup form and any app settings.

Owner: Ifreen

Calls db.auth (Rabia) for the actual auth calls — this file only
handles the Streamlit widgets and session_state.
"""

import streamlit as st

from db.auth import sign_in, sign_up


def render_sidebar() -> None:
    st.sidebar.title("Account")

    if st.session_state.get("user"):
        st.sidebar.write(f"Signed in as {st.session_state['user']['email']}")
        if st.sidebar.button("Sign out"):
            st.session_state.pop("user", None)
            st.rerun()
        return

    tab_login, tab_signup = st.sidebar.tabs(["Log in", "Sign up"])

    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Log in"):
            # TODO(Ifreen, once Rabia's sign_in is implemented): call it
            # and store the result in st.session_state["user"].
            st.info("Wire this up once db.auth.sign_in is implemented.")

    with tab_signup:
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_password")
        if st.button("Sign up"):
            st.info("Wire this up once db.auth.sign_up is implemented.")
