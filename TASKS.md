# Task Division

Three tracks. The contracts below (function names + what they return) are
what let them integrate without stepping on each other.

## Ghanwa — Chat engine, Gemini, RAG (`core/`, `tools/`, `rag/`)

| File | What it does |
|---|---|
| `core/gemini_client.py` | Gemini SDK setup (`google-genai`), `get_model(tools=...)` |
| `core/chat_engine.py` | `send_message(user_id, user_text) -> str` (async) — the full turn: history, tool-calling loop, persistence |
| `core/prompts.py` | System prompt + RAG grounding instructions |
| `core/stt.py` / `core/tts.py` | Speech via Gemini's native audio support (no separate STT/TTS provider) |
| `core/exceptions.py` | Shared exception hierarchy used across the whole backend |
| `tools/tool_registry.py` | Decorator-based tool registration (`@register(...)`) |
| `tools/weather.py`, `tools/calculator.py` | Built-in tools (weather via Open-Meteo — no API key needed) |
| `rag/` | Document upload -> chunk -> embed -> retrieve -> grounded answer pipeline |

Originally prototyped against local SQLite + a FastAPI server (`main.py`, still in ghanwa-branch's history if a standalone API is ever needed) — ported to call Supabase directly so the whole app runs as one Streamlit process. Only `db/chat_history.py`, `db/documents.py`, and `rag/vector_store.py` changed for that; everything else here was already storage-agnostic and needed no changes.

## Rabia — Supabase: persistence, auth, face login, tools infra (`db/`)

| File | What it does |
|---|---|
| `config/settings.py` | Single source of config (pydantic-settings, reads `.env`) |
| `db/supabase_client.py` | Shared Supabase client |
| `db/schema.sql` | `messages`, `face_encodings`, `documents`, `chunks` tables + RLS — run in the Supabase SQL editor |
| `db/auth.py` | sign up, log in, log out, restore session, forgot password |
| `db/face_auth.py` | face-recognition sign-up/login (128-d encoding via `face_recognition`, never stores the photo) |
| `db/chat_history.py` | `add_message` / `get_recent_messages` — backs `core/chat_engine.py` |
| `db/documents.py` | document metadata — backs `rag/rag_service.py` |

**Setup**: `face_recognition` wraps `dlib`, which needs CMake + a C++ build toolchain on Windows (see `requirements.txt`). `pydub` (used by `core/tts.py`) needs `ffmpeg` installed and on PATH — on Windows: `winget install --id Gyan.FFmpeg -e`, then restart your shell.

## Ifreen — Frontend (`frontend/`)

Built independently as its own app (`frontend/app.py`, `frontend/pages/`, `frontend/components/`) rather than filling in the original `ui/` scaffold — that's fine, `ui/` and the root `app.py` are stale now and can be deleted.

Currently wired to `frontend/utils/mock_api.py` (fake responses) instead of the real backend. The function names already line up closely with the real ones, so swapping should be mechanical:

| Mock function | Real replacement |
|---|---|
| `login_user(email, password)` | `db.auth.sign_in(email, password)` |
| `signup_user(...)` | `db.auth.sign_up(email, password)` then `db.face_auth.register_face(user_id, face_bytes)` if a face photo was captured |
| `verify_face(image_bytes)` | `db.face_auth.verify_face(image_bytes)` — same name already |
| `send_chat_message(message, ...)` | `asyncio.run(core.chat_engine.send_message(user_id, message))` — note: async, needs the `asyncio.run` wrapper since Streamlit itself is sync |
| `upload_document(file)` | `asyncio.run(rag.rag_service.ingest_document(user_id, file.name, file.type, file.getvalue()))` |

## Architecture note

Originally considered a separate FastAPI backend (Ghanwa had one working). Decided against it for this deployment: one Streamlit process is simpler to deploy reliably (one hosting target, one set of env vars, no cross-service network calls, tokens, or CORS to get wrong) than coordinating two separately-hosted services. `main.py` stays available in `ghanwa-branch`'s history if a real standalone API is ever needed later (e.g. a mobile client).

## Setup for everyone

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # fill in your API keys
streamlit run frontend/app.py
```

Run the test suite with `pytest` (uses mocks throughout — no real API keys or database needed to run it, except the RAG vector-store test which uses an in-memory fake Supabase double, not the real project).
