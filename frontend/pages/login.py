"""
Screen 2 — Login

Recreates the exact visual design of the Login reference image.
Compact split layout using Streamlit columns and containers.
Fits entirely inside a single viewport (~1366x768) with no page scrolling.
"""

import streamlit as st
from components.ui_components import logo_mark, password_field
from utils.mock_api import login_user


def render() -> None:
    main_col1, main_col2 = st.columns([1, 1.15], gap="medium")

    # ---- Left Column: Brand & Illustration Panel -----------------------------
    with main_col1:
        with st.container(key="auth_brand_panel"):
            logo_mark(size=44)
            st.markdown(
                """
                <div class="brand-heading">Welcome<br/>back</div>
                <div class="brand-subtitle">Login to continue your AI chat experience.</div>
                """,
                unsafe_allow_html=True,
            )

            # Modern chair / interior illustration matching design reference 2
            st.markdown(
                """
                <div class="brand-illustration">
                    <svg width="220" height="170" viewBox="0 0 240 180" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <ellipse cx="120" cy="160" rx="90" ry="12" fill="#EEF2FF"/>
                        <!-- Soft blue armchair -->
                        <path d="M70 110C70 95 85 90 120 90C155 90 170 95 170 110V140H70V110Z" fill="#93C5FD"/>
                        <path d="M80 70C80 60 95 55 120 55C145 55 160 60 160 70V100H80V70Z" fill="#60A5FA"/>
                        <!-- Armrests -->
                        <rect x="60" y="95" width="20" height="40" rx="8" fill="#3B82F6"/>
                        <rect x="160" y="95" width="20" height="40" rx="8" fill="#3B82F6"/>
                        <!-- Legs -->
                        <line x1="80" y1="140" x2="72" y2="160" stroke="#64748B" stroke-width="3" stroke-linecap="round"/>
                        <line x1="160" y1="140" x2="168" y2="160" stroke="#64748B" stroke-width="3" stroke-linecap="round"/>
                        <!-- Small plant table next to chair -->
                        <rect x="190" y="125" width="26" height="4" rx="2" fill="#CBD5E1"/>
                        <line x1="195" y1="129" x2="192" y2="158" stroke="#94A3B8" stroke-width="2"/>
                        <line x1="211" y1="129" x2="214" y2="158" stroke="#94A3B8" stroke-width="2"/>
                        <path d="M198 125C198 115 208 115 208 125H198Z" fill="#34D399"/>
                    </svg>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ---- Right Column: Form Card ---------------------------------------------
    with main_col2:
        with st.container(key="auth_form_card"):
            success_msg = st.session_state.pop("signup_success_message", None)
            if success_msg:
                st.success(success_msg)

            st.text_input("Email Address", key="login_email", placeholder="Enter your email")

            password = password_field("Password", key="login_password", placeholder="Enter your password")

            # Forgot password row
            st.markdown(
                '<div style="text-align: right; margin-top: -0.4rem; margin-bottom: 0.6rem;">'
                '<span class="forgot-link">Forgot password?</span></div>',
                unsafe_allow_html=True,
            )

            error_placeholder = st.empty()

            if st.button("Login", type="primary", key="login_submit", use_container_width=True):
                email_val = st.session_state.get("login_email", "").strip()
                result = login_user(email_val, password)
                if result["success"]:
                    st.session_state.user = result["user"]
                    st.session_state.page = "chatbot"
                    st.session_state.chat_history = []
                    st.rerun()
                else:
                    error_placeholder.markdown(
                        f'<div class="chat-error">⚠️ {result["message"]}</div>',
                        unsafe_allow_html=True,
                    )

            st.markdown('<div class="auth-divider"><span>or</span></div>', unsafe_allow_html=True)

            if st.button("📷  Login with Face", key="login_with_face", use_container_width=True):
                st.session_state.page = "face_login"
                st.session_state.face_state = "idle"
                st.rerun()

            st.markdown('<div class="auth-footer-text">Don\'t have an account?</div>', unsafe_allow_html=True)
            if st.button("Sign up", key="login_goto_signup", use_container_width=True):
                st.session_state.page = "signup"
                st.rerun()
