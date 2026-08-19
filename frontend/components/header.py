"""
Header for the main chat area.
Matches design reference 4 header.
"""

import streamlit as st


def render_header() -> None:
    title = st.session_state.get("active_conversation", "Project Summary")
    st.markdown(
        f"""
        <div class="chat-header-bar">
            <div class="header-left">
                <span class="header-title">{title}</span>
                <span class="header-dropdown-icon">⌄</span>
            </div>
            <div class="header-right-actions">
                <span class="header-action-btn" title="Search">🔍</span>
                <span class="header-action-btn" title="Share">⤴</span>
                <span class="header-action-btn" title="More options">⋯</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
