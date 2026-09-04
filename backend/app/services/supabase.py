"""Reusable Supabase client access."""

from supabase import Client, ClientOptions, create_client

from app.core.config import get_supabase_settings


_supabase_client: Client | None = None


def get_supabase_client() -> Client:
    """Return the process-wide Supabase client, creating it on first use."""
    global _supabase_client

    if _supabase_client is None:
        settings = get_supabase_settings()
        _supabase_client = create_client(settings.url, settings.key)

    return _supabase_client


def get_authenticated_supabase_client(access_token: str) -> Client:
    """Create a request-scoped client whose database calls use the user's JWT.

    A separate client avoids mutating the shared Auth client between requests.
    """
    settings = get_supabase_settings()
    return create_client(
        settings.url,
        settings.key,
        options=ClientOptions(
            headers={"Authorization": f"Bearer {access_token}"},
            auto_refresh_token=False,
            persist_session=False,
        ),
    )
