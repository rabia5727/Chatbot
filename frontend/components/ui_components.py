"""
Small, reusable UI building blocks shared across pages.
"""

import streamlit as st

from components.icons import alert_triangle, speaker


def logo_mark(size: int = 44, centered: bool = False) -> None:
    """Renders a simple abstract, text-free logo mark (no product name)."""
    wrap_class = "logo-mark-wrap centered" if centered else "logo-mark-wrap"
    svg = f"""
    <div class="{wrap_class}">
        <svg width="{size}" height="{size}" viewBox="0 0 44 44" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="2" y="2" width="40" height="40" rx="14" fill="#EEF2FF" stroke="#4F46E5" stroke-width="1.5"/>
            <circle cx="18" cy="22" r="6" fill="#4F46E5"/>
            <circle cx="28" cy="14" r="3.2" fill="#4F46E5" fill-opacity="0.55"/>
        </svg>
    </div>
    """
    st.markdown(svg, unsafe_allow_html=True)


def password_field(
    label: str,
    key: str,
    help_text: str | None = None,
    placeholder: str | None = None,
) -> str:
    """A plain password input (masked, no visibility toggle)."""
    return st.text_input(
        label,
        type="password",
        key=key,
        help=help_text,
        placeholder=placeholder or "Enter password",
    )


def password_strength_meter(password: str) -> None:
    """Renders a simple visual strength bar under a password field."""
    if not password:
        return

    score = 0
    if len(password) >= 8:
        score += 1
    if any(c.isupper() for c in password):
        score += 1
    if any(c.isdigit() for c in password):
        score += 1
    if any(not c.isalnum() for c in password):
        score += 1

    levels = [
        ("Weak", "#DC2626", "25%"),
        ("Fair", "#F59E0B", "50%"),
        ("Good", "#4F46E5", "75%"),
        ("Strong", "#16A34A", "100%"),
    ]
    label, color, width = levels[max(score - 1, 0)]

    st.markdown(
        f"""
        <div class="pw-strength-track">
            <div class="pw-strength-fill" style="width:{width}; background:{color};"></div>
        </div>
        <div class="pw-strength-label">Password strength: <b style="color:{color}">{label}</b></div>
        """,
        unsafe_allow_html=True,
    )


def status_pill(label: str, variant: str = "idle") -> None:
    """variant: idle | processing | success | failure"""
    st.markdown(f'<span class="status-pill {variant}">{label}</span>', unsafe_allow_html=True)


def typing_indicator() -> None:
    st.markdown(
        '<div class="typing-indicator"><span></span><span></span><span></span></div>',
        unsafe_allow_html=True,
    )


def chat_error(message: str = "Something went wrong. Please try again.") -> None:
    st.markdown(f'<div class="chat-error">{alert_triangle(16)} {message}</div>', unsafe_allow_html=True)


def voice_listening_indicator() -> None:
    st.markdown(
        '<div class="voice-indicator"><span class="pulse-dot"></span> Listening...</div>',
        unsafe_allow_html=True,
    )


def tts_playing_indicator() -> None:
    st.markdown(
        f'<div class="tts-indicator">{speaker(16)} Playing response</div>',
        unsafe_allow_html=True,
    )
