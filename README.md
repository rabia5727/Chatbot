# Chatbot

Streamlit + Gemini + Supabase chatbot with voice input/output, face-recognition
login, and document Q&A (RAG) via Gemini function calling.

See [TASKS.md](TASKS.md) for who owns what and how the pieces fit together.

## Project layout

```
chatbot/
├── frontend/            # Ifreen: the actual UI (Streamlit multi-screen app)
│   ├── app.py             # entry point — run this
│   ├── pages/              # signup, login, face_login, chatbot screens
│   ├── components/          # reusable UI pieces
│   └── utils/mock_api.py     # placeholder backend calls (being wired to the real backend)
├── core/                 # Ghanwa: Gemini client, chat engine, STT/TTS
├── tools/                 # Ghanwa: function-calling tools (weather, calculator)
├── rag/                    # Ghanwa: document ingestion + retrieval-augmented Q&A
├── db/                      # Rabia: Supabase persistence, auth, face login
├── config/                   # shared settings (reads .env)
├── tests/
└── app.py, ui/                # stale — superseded by frontend/, can be deleted
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Fill in `.env`:
- `GEMINI_API_KEY` — from Google AI Studio
- `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_KEY` — from your Supabase project settings (URL/API page). `SUPABASE_KEY` is the **publishable/anon** key; `SUPABASE_SERVICE_KEY` is the **secret/service_role** key, used only server-side for face-login matching — never expose it anywhere else.

Run `db/schema.sql` in your Supabase project's SQL editor to create the required tables (`messages`, `face_encodings`, `documents`, `chunks`), each with Row Level Security so users only ever see their own data.

Weather lookup (`tools/weather.py`) uses Open-Meteo, which needs no API key.

Face recognition (`db/face_auth.py`) needs `face_recognition`, which wraps `dlib` — on Windows this needs CMake + a C++ build toolchain to compile (or `conda install -c conda-forge dlib` first).

Text-to-speech (`core/tts.py`) needs `ffmpeg` on your system PATH (not a Python package). On Windows: `winget install --id Gyan.FFmpeg -e`, then restart your terminal.

Run the app:

```bash
streamlit run frontend/app.py
```

Run the tests:

```bash
pytest
```

## Adding a new tool

Add a file in `tools/` with a function decorated with `@register(name=..., description=..., parameters=...)` from `tools.tool_registry` (see `tools/weather.py` for the pattern), then add its module name to `_BUILTIN_MODULES` in `tools/__init__.py`. `core/chat_engine.py` picks it up automatically.
