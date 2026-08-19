"""
Supabase client singleton.

Owner: Rabia

Everything else in db/ imports `supabase` from here instead of creating
its own client.
"""

from supabase import Client, create_client

from config.settings import get_settings

_settings = get_settings()
supabase: Client = create_client(_settings.supabase_url, _settings.supabase_key)
