"""
Optional custom CSS / theming.

Owner: Ifreen
"""

import streamlit as st


def inject_custom_css() -> None:
    st.markdown(
        """
        <style>
        /* TODO(Ifreen): add custom styling here */
        </style>
        """,
        unsafe_allow_html=True,
    )
