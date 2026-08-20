"""
Screen 1 — Sign Up with Face Enrollment

Recreates the exact visual design of the Sign Up reference image.
Includes Face Enrollment section for setting up Face Login during signup.
Compact split layout using Streamlit columns and containers.
Fits entirely inside a single viewport (~1366x768) with no page scrolling.
"""

import streamlit as st
from components.icons import alert_triangle
from components.ui_components import logo_mark, password_field, password_strength_meter
from utils.backend import signup_user, enroll_face


def render() -> None:
    main_col1, main_col2 = st.columns([1, 1.15], gap="medium")

    # ---- Left Column: Brand & Illustration Panel -----------------------------
    with main_col1:
        with st.container(key="auth_brand_panel"):
            logo_mark(size=44)
            st.markdown(
                """
                <div class="brand-heading">Create your account</div>
                <div class="brand-subtitle">Join us and start your AI chat experience.</div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                """
                <div class="brand-illustration">
                    <svg width="220" height="160" viewBox="0 0 240 180" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M0 140C60 120 100 160 160 130C200 110 220 140 240 130V180H0V140Z" fill="#EEF2FF"/>
                        <path d="M20 150C80 135 120 165 180 145C210 135 230 155 240 150V180H20V150Z" fill="#E0E7FF"/>
                        <rect x="70" y="115" width="24" height="25" rx="4" fill="#94A3B8"/>
                        <path d="M82 115C82 95 65 85 60 75C70 85 82 95 82 115Z" fill="#10B981"/>
                        <path d="M82 115C82 90 98 80 105 70C95 80 82 90 82 115Z" fill="#059669"/>
                        <path d="M82 115C82 100 75 90 70 85C78 92 82 102 82 115Z" fill="#34D399"/>
                    </svg>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ---- Right Column: Form Card ---------------------------------------------
    with main_col2:
        with st.container(key="auth_form_card"):
            # Face enrollment lives outside the form below -- st.camera_input
            # doesn't work well inside st.form, and enrolling gives its own
            # immediate feedback as a separate pre-step.
            st.markdown(
                '<div style="margin-top:0.4rem; font-weight:700; font-size:0.84rem; color:var(--text-primary); display:flex; align-items:center; gap:0.4rem;">'
                '<span></span> <span>Set up Face Login</span></div>',
                unsafe_allow_html=True,
            )
            st.caption("Capture your face to enable face login.")

            with st.expander("Camera for Face Enrollment", expanded=False):
                enroll_camera = st.camera_input("Enroll Face", label_visibility="collapsed", key="signup_face_camera")
                if enroll_camera is not None:
                    st.session_state.signup_face_bytes = enroll_camera.getvalue()
                    enroll_res = enroll_face(st.session_state.signup_face_bytes)
                    st.success(enroll_res["message"])

            # Everything the account actually needs is inside one form, so
            # "Create Account" reads every field's current value atomically
            # at submit time -- without a form, a field you just typed into
            # (and never clicked away from) can still read as empty, since
            # Streamlit only syncs a text_input's value on blur/Enter.
            with st.form(key="signup_form", border=False):
                st.text_input("Full Name", key="signup_full_name", placeholder="Enter your full name")
                st.text_input("Email Address", key="signup_email", placeholder="Enter your email")

                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    password = password_field("Password", key="signup_password", placeholder="Create a password")
                with col_p2:
                    confirm_password = password_field("Confirm Password", key="signup_confirm_password", placeholder="Confirm your password")

                password_strength_meter(password)

                agree = st.checkbox("I agree to the Terms of Service and Privacy Policy", key="signup_terms")

                error_placeholder = st.empty()

                submitted = st.form_submit_button(
                    "Create Account", type="primary", use_container_width=True
                )

            if submitted:
                full_name_val = st.session_state.get("signup_full_name", "").strip()
                email_val = st.session_state.get("signup_email", "").strip()
                face_bytes = st.session_state.get("signup_face_bytes")

                if not full_name_val or not email_val or not password or not confirm_password:
                    error_placeholder.markdown(
                        f'<div class="chat-error">{alert_triangle(16)} Please fill in every required field.</div>',
                        unsafe_allow_html=True,
                    )
                elif password != confirm_password:
                    error_placeholder.markdown(
                        f'<div class="chat-error">{alert_triangle(16)} Passwords do not match.</div>',
                        unsafe_allow_html=True,
                    )
                elif not agree:
                    error_placeholder.markdown(
                        f'<div class="chat-error">{alert_triangle(16)} Please accept the Terms and Privacy Policy.</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    # TODO: Send captured image to backend for face enrollment.
                    # The backend teammate will process the face, create the face embedding,
                    # save it to the database, and associate it with the user account.
                    result = signup_user(full_name_val, email_val, password, face_image_bytes=face_bytes)
                    if result["success"]:
                        st.session_state.page = "login"
                        st.session_state.signup_success_message = result["message"]
                        st.rerun()
                    else:
                        error_placeholder.markdown(
                            f'<div class="chat-error">{alert_triangle(16)} {result["message"]}</div>',
                            unsafe_allow_html=True,
                        )

            st.markdown('<div class="auth-footer-text">Already have an account?</div>', unsafe_allow_html=True)
            if st.button("Login", key="signup_goto_login", use_container_width=True):
                st.session_state.page = "login"
                st.rerun()
