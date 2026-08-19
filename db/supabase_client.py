"""
Supabase client singleton.

Owner: Rabia

Everything else in db/ imports `supabase` from here instead of creating
its own client.
"""

from supabase import Client, create_client

from config import SUPABASE_KEY, SUPABASE_URL

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
