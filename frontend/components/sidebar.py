"""
Left sidebar for the chatbot screen: new chat, search, grouped
conversation list, and a user section pinned to the bottom.
"""

import streamlit as st

MOCK_CONVERSATIONS = {
    "Today": [
        ("Project Summary", "10:30 AM"),
        ("Python Help", "9:15 AM"),
        ("Weather in Karachi", "8:45 AM"),
    ],
    "Yesterday": [
        ("Document Analysis", "Tue"),
        ("AI Capabilities", "Tue"),
    ],
}


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="sb-brand-row">
                <svg width="28" height="28" viewBox="0 0 44 44" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="2" y="2" width="40" height="40" rx="14" fill="#EEF2FF" stroke="#4F46E5" stroke-width="1.5"/>
                    <circle cx="18" cy="22" r="6" fill="#4F46E5"/>
                    <circle cx="28" cy="14" r="3.2" fill="#4F46E5" fill-opacity="0.55"/>
                </svg>
                <span class="sb-brand-title">AI Assistant</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("+ New Chat", type="primary", key="new_chat_btn", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.active_conversation = "Project Summary"
            st.rerun()

        st.text_input(
            "Search conversations",
            key="convo_search",
            placeholder="Search conversations",
            label_visibility="collapsed",
        )

        active = st.session_state.get("active_conversation", "Project Summary")
        query = st.session_state.get("convo_search", "").strip().lower()

        # Conversation list area
        for group_label, conversations in MOCK_CONVERSATIONS.items():
            visible = [(c, t) for c, t in conversations if query in c.lower()] if query else conversations
            if not visible:
                continue
            st.markdown(f'<div class="sb-group-label">{group_label}</div>', unsafe_allow_html=True)
            for convo, time_str in visible:
                is_active = (convo == active)
                btn_label = f"💬  {convo}"
                if st.button(btn_label, key=f"convo_{group_label}_{convo}", use_container_width=True):
                    st.session_state.active_conversation = convo
                    st.session_state.chat_history = []
                    st.rerun()

        st.markdown('<div style="flex-grow: 1;"></div>', unsafe_allow_html=True)

        user = st.session_state.get("user") or {"name": "Ifreen", "email": "ifreen@example.com"}
        user_name = user.get("name", "Ifreen")
        user_email = user.get("email", "ifreen@example.com")
        initials = "".join([p[0] for p in user_name.split()[:2]]).upper() or "IF"

        st.markdown(
            f"""
            <div class="sb-user-card">
                <div class="sb-avatar">{initials}</div>
                <div class="sb-user-info">
                    <div class="sb-user-name">{user_name}</div>
                    <div class="sb-user-email">{user_email}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("Log out", key="logout_btn", use_container_width=True):
            st.session_state.user = None
            st.session_state.page = "login"
            st.session_state.chat_history = []
            st.rerun()
