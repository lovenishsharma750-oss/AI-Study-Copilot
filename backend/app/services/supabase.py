"""Reusable Supabase client access."""

from supabase import Client, create_client

from app.core.config import get_supabase_settings


_supabase_client: Client | None = None


def get_supabase_client() -> Client:
    """Return the process-wide Supabase client, creating it on first use."""
    global _supabase_client

    if _supabase_client is None:
        settings = get_supabase_settings()
        _supabase_client = create_client(settings.url, settings.key)

    return _supabase_client
