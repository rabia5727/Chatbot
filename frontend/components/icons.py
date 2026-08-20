"""
Small inline SVG icons used in place of emoji throughout the UI.

Emoji render inconsistently across OS/browsers (different art style,
color, even missing glyphs) and look out of place next to the app's flat
indigo/gray design. These are plain stroke-based line icons instead --
same visual language as logo_mark()'s SVG, sized to sit inline with text.

Usage: interpolate directly into an f-string passed to st.markdown(...,
unsafe_allow_html=True), e.g. f'<span class="guide-icon">{lightbulb()}</span>'.
"""

_DEFAULT_COLOR = "currentColor"


def _svg(inner: str, size: int = 18, color: str = _DEFAULT_COLOR, stroke_width: float = 2) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" '
        f'stroke-linejoin="round" style="vertical-align:-3px">{inner}</svg>'
    )


def search(size: int = 18, color: str = _DEFAULT_COLOR) -> str:
    return _svg('<circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>', size, color)


def lock(size: int = 18, color: str = _DEFAULT_COLOR) -> str:
    return _svg(
        '<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
        size,
        color,
    )


def lightbulb(size: int = 18, color: str = _DEFAULT_COLOR) -> str:
    return _svg(
        '<path d="M9 18h6"/><path d="M10 22h4"/>'
        '<path d="M12 2a7 7 0 0 0-4 12.7V17h8v-2.3A7 7 0 0 0 12 2z"/>',
        size,
        color,
    )


def check_circle(size: int = 18, color: str = _DEFAULT_COLOR) -> str:
    return _svg('<circle cx="12" cy="12" r="10"/><path d="M8 12l3 3 5-6"/>', size, color)


def x_circle(size: int = 18, color: str = _DEFAULT_COLOR) -> str:
    return _svg(
        '<circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/>'
        '<line x1="9" y1="9" x2="15" y2="15"/>',
        size,
        color,
    )


def document(size: int = 18, color: str = _DEFAULT_COLOR) -> str:
    return _svg(
        '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>'
        '<polyline points="14 2 14 8 20 8"/>',
        size,
        color,
    )


def cloud(size: int = 18, color: str = _DEFAULT_COLOR) -> str:
    return _svg(
        '<path d="M17.5 19a4.5 4.5 0 0 0 0-9 6 6 0 0 0-11.6 1.5A4 4 0 0 0 6 19h11.5z"/>',
        size,
        color,
    )


def chat(size: int = 18, color: str = _DEFAULT_COLOR) -> str:
    return _svg(
        '<path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 '
        '8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 '
        '8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>',
        size,
        color,
    )


def speaker(size: int = 18, color: str = _DEFAULT_COLOR) -> str:
    return _svg(
        '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>'
        '<path d="M15.5 8.5a5 5 0 0 1 0 7"/><path d="M18 6a9 9 0 0 1 0 12"/>',
        size,
        color,
    )


def camera(size: int = 18, color: str = _DEFAULT_COLOR) -> str:
    return _svg(
        '<path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>'
        '<circle cx="12" cy="13" r="4"/>',
        size,
        color,
    )


def eye(size: int = 18, color: str = _DEFAULT_COLOR) -> str:
    return _svg(
        '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>',
        size,
        color,
    )


def alert_triangle(size: int = 18, color: str = _DEFAULT_COLOR) -> str:
    return _svg(
        '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3'
        'L13.71 3.86a2 2 0 0 0-3.42 0z"/>'
        '<line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
        size,
        color,
    )
