# Chatbot

Streamlit + Gemini + Supabase chatbot with voice input/output (STT/TTS)
and external-tool support (starting with weather) via Gemini function
calling.

See [TASKS.md](TASKS.md) for who owns what and how the pieces fit together.

## Project layout

```
chatbot/
├── app.py              # Streamlit entry point — wires everything together
├── config.py            # loads .env into shared constants
├── core/                 # Ghanwa: Gemini calls, chat orchestration, STT, TTS
├── db/                    # Rabia: Supabase client, auth, chat history
├── tools/                 # Rabia: function-calling tools (weather, ...)
├── ui/                     # Ifreen: Streamlit widgets (chat, sidebar, voice, audio)
├── utils/                  # shared helpers
├── tests/
└── .streamlit/config.toml   # theme
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
- `SUPABASE_URL`, `SUPABASE_KEY` — from your Supabase project settings
- `WEATHER_API_KEY` — from whichever weather API you pick (e.g. OpenWeatherMap)

Run the app:

```bash
streamlit run app.py
```

## Adding a new external tool

1. Add a file in `tools/` with a single function, e.g. `tools/news_tool.py`.
2. Register it in `tools/tool_registry.py`: add its Gemini function
   declaration to `TOOL_DECLARATIONS` and map its name to the function
   in `TOOL_FUNCTIONS`.

No changes needed anywhere else — `core/chat_engine.py` picks up new
tools automatically through the registry.
