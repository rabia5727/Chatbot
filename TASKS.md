# Task Division

Three tracks, split so each person can build and test their part mostly
independently. The contracts below (function names + what they return)
are what let the three tracks integrate without stepping on each other —
don't change a signature without telling whoever calls it.

## Ghanwa — LLM Core & Voice (`core/`)

| File | What to build |
|---|---|
| `core/gemini_client.py` | Configure the Gemini SDK, expose `get_model(tools=None)` |
| `core/prompts.py` | System prompt / prompt templates |
| `core/chat_engine.py` | `send_message(user_id, user_text) -> str` — the full turn: call Gemini, resolve function calls via `tools.tool_registry.dispatch`, save via `db.chat_history`, return the reply text |
| `core/stt.py` | `transcribe(audio_bytes) -> str` |
| `core/tts.py` | `synthesize(text) -> bytes` (mp3) |

Depends on: `tools.tool_registry.get_tool_declarations()` / `dispatch()` (Rabia), `db.chat_history.get_history()` / `save_message()` (Rabia).
Can build/test this in isolation with a small script calling `chat_engine.send_message` directly — don't need the UI running.

## Rabia — Data & Tools (`db/`, `tools/`)

| File | What to build |
|---|---|
| `db/supabase_client.py` | Already stubbed — just needs `SUPABASE_URL`/`SUPABASE_KEY` in `.env` |
| `db/schema.sql` | Run in Supabase SQL editor to create the `messages` table (already drafted, adjust as needed) |
| `db/auth.py` | `sign_up`, `sign_in`, `sign_out`, `get_current_user` |
| `db/chat_history.py` | `save_message(user_id, role, content)`, `get_history(user_id, limit) -> list[dict]` |
| `tools/weather_tool.py` | `get_weather(city) -> str` using a weather API |
| `tools/tool_registry.py` | Already scaffolded — register new tools here as you add them (declaration + function mapping) |

This is also where new external tools (beyond weather) get added later — each new tool is one file in `tools/` plus two lines in `tool_registry.py`.

## Ifreen — UI & Integration (`ui/`, `app.py`)

| File | What to build |
|---|---|
| `ui/chat_ui.py` | Render message history |
| `ui/sidebar.py` | Login/signup form (wires to `db.auth` once Rabia's done) |
| `ui/voice_input.py` | Mic widget -> `core.stt.transcribe` |
| `ui/audio_output.py` | Play TTS reply -> `core.tts.synthesize` |
| `ui/styles.py` | Theming/CSS |
| `app.py` | Wires all three tracks together into the running app |

## Suggested order

1. Everyone stubs their functions first (mostly done already) so imports don't break.
2. Rabia: get Supabase project created, run `schema.sql`, get `chat_history.py` working — this unblocks Ghanwa.
3. Ghanwa: get a basic Gemini call working in `chat_engine.py` (even without tools/history) so Ifreen can test the UI end-to-end early.
4. Wire in function calling (weather tool) and STT/TTS once the basic loop works.
5. Auth last — the app can work with a hardcoded `demo-user` id until then (already set up that way in `app.py`).

## Setup for everyone

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # fill in your API keys
streamlit run app.py
```
