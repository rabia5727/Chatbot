"""
Screen 3 — Face Login / Face Verification

Recreates the exact visual design of the Face Verification reference image.
Only reachable from Login -> "Login with Face".
Compact split layout using Streamlit columns and containers.
Fits entirely inside a single viewport (~1366x768) with no page scrolling.
"""

import streamlit as st
from components.icons import camera, check_circle, eye, lightbulb, lock, x_circle
from components.ui_components import logo_mark
from utils.backend import verify_face


def render() -> None:
    if "face_state" not in st.session_state:
        st.session_state.face_state = "idle"  # idle | camera_active | success | failure

    # Top back button row
    if st.button("Back to Login", icon=":material/arrow_back:", key="face_back_top"):
        st.session_state.page = "login"
        st.session_state.face_state = "idle"
        st.rerun()

    main_col1, main_col2 = st.columns([1, 1.25], gap="medium")

    state = st.session_state.face_state

    # ---- Left Column: Guidance & Instructions --------------------------------
    with main_col1:
        st.markdown('<div class="brand-heading" style="margin-top:0.5rem;">Login with Face</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="brand-subtitle">We will verify your identity using face recognition.</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="face-guide-card">
                <div class="guide-icon">{camera(20)}</div>
                <div>
                    <div class="guide-title">Position your face inside the frame</div>
                    <div class="guide-sub">Keep your head centered in the camera view</div>
                </div>
            </div>
            <div class="face-guide-card">
                <div class="guide-icon">{eye(20)}</div>
                <div>
                    <div class="guide-title">Make sure your face is clearly visible</div>
                    <div class="guide-sub">Avoid hats, dark glasses or heavy shadows</div>
                </div>
            </div>
            <div class="face-guide-card">
                <div class="guide-icon">{lightbulb(20)}</div>
                <div>
                    <div class="guide-title">Good lighting helps us recognize you</div>
                    <div class="guide-sub">Ensure room is well illuminated</div>
                </div>
            </div>

            <div class="privacy-note">{lock(14)} We never store your face image.</div>
            """,
            unsafe_allow_html=True,
        )

    # ---- Right Column: Camera Viewfinder & Result Card -----------------------
    with main_col2:
        with st.container(key="face_camera_card"):
            if state == "idle":
                # Camera stays off until the user explicitly asks for it --
                # st.camera_input activates the webcam the moment it's
                # rendered, so it must not be on screen before this click.
                st.markdown(
                    '<div class="camera-status-row off">'
                    '<span class="pulse-dot-gray"></span> <span>Camera is off</span></div>',
                    unsafe_allow_html=True,
                )
                if st.button(
                    "Start Camera", type="primary", key="start_face_camera", use_container_width=True
                ):
                    st.session_state.face_state = "camera_active"
                    st.rerun()

            elif state == "camera_active":
                captured_image = st.camera_input("Camera", label_visibility="collapsed", key="face_camera")

                st.markdown('<div class="camera-status-row"><span class="pulse-dot-green"></span> <span>Camera is active</span></div>', unsafe_allow_html=True)

                col_verify, col_cancel = st.columns(2)
                with col_verify:
                    if st.button(
                        "Verify Face", type="primary", key="verify_face_btn", use_container_width=True
                    ):
                        with st.spinner("Verifying your identity..."):
                            image_bytes = captured_image.getvalue() if captured_image is not None else None

                            # TODO: Send captured image to backend for face authentication.
                            # The backend teammate will compare the face embedding against stored profiles in DB and return:
                            #   {"success": true} or {"success": false}
                            result = verify_face(image_bytes)

                        if result["success"]:
                            st.session_state.face_state = "success"
                            st.session_state.face_verified_user = result["user"]
                        else:
                            st.session_state.face_state = "failure"
                        st.rerun()
                with col_cancel:
                    if st.button("Cancel", key="cancel_face_camera", use_container_width=True):
                        # Turns the camera back off -- dropping the
                        # camera_input widget from the page releases it.
                        st.session_state.face_state = "idle"
                        st.rerun()

            elif state == "success":
                st.markdown(
                    f"""
                    <div class="verify-result-box success">
                        <div class="result-icon">{check_circle(40, "#16A34A")}</div>
                        <div class="result-title">Identity verified!</div>
                        <div class="result-sub">Welcome back.</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("Continue to Chat", type="primary", key="face_continue_chat", use_container_width=True):
                    # Use the real verified user (id/email/tokens) as-is --
                    # not a placeholder -- so chat history and RLS work.
                    st.session_state.user = st.session_state.get("face_verified_user")
                    st.session_state.page = "chatbot"
                    st.session_state.chat_history = []
                    st.session_state.face_state = "idle"
                    st.rerun()

            elif state == "failure":
                st.markdown(
                    f"""
                    <div class="verify-result-box failure">
                        <div class="result-icon">{x_circle(40, "#DC2626")}</div>
                        <div class="result-title">Face not recognized</div>
                        <div class="result-sub">Please try again or log in with password.</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                fc1, fc2 = st.columns(2)
                with fc1:
                    if st.button("Try Again", type="primary", key="face_try_again", use_container_width=True):
                        st.session_state.face_state = "idle"
                        st.rerun()
                with fc2:
                    if st.button("Back to Login", key="face_back_bottom", use_container_width=True):
                        st.session_state.page = "login"
                        st.session_state.face_state = "idle"
                        st.rerun()
