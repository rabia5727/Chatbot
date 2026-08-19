"""
Shared config loader. Everyone imports from here instead of calling
os.getenv() directly, so there's one place that knows about env vars.

Owner: Ifreen (shared file — ping the group before changing keys)
"""

import os

from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# service_role/secret key — privileged, used ONLY by db/face_auth.py to
# match a login photo against every user's stored face. Never expose
# this anywhere else (no UI, no logs, no committing it to git).
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")

APP_NAME = "Cognify Chatbot"  # placeholder, rename freely
