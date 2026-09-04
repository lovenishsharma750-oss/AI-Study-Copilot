"""Supabase email/password authentication operations."""

from app.schemas.auth import AuthResponse, AuthUserResponse, SessionResponse
from app.services.supabase import get_supabase_client


class AuthenticationError(Exception):
    """Raised when Supabase Auth cannot complete an authentication operation."""


def _to_auth_response(auth_response: object) -> AuthResponse:
    """Convert a Supabase Auth response into the deliberately small API response."""
    user = getattr(auth_response, "user", None)
    if user is None or not getattr(user, "id", None):
        raise AuthenticationError()

    session = getattr(auth_response, "session", None)
    session_response = None
    if session is not None:
        session_response = SessionResponse(
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            expires_at=getattr(session, "expires_at", None),
            expires_in=getattr(session, "expires_in", None),
            token_type=getattr(session, "token_type", None),
        )

    return AuthResponse(
        user=AuthUserResponse(id=str(user.id), email=getattr(user, "email", None)),
        session=session_response,
    )


def signup(*, name: str, email: str, password: str) -> AuthResponse:
    """Create a Supabase Auth user and let the database trigger create its profile."""
    try:
        auth_response = get_supabase_client().auth.sign_up(
            {
                "email": email,
                "password": password,
                "options": {"data": {"full_name": name}},
            }
        )
        return _to_auth_response(auth_response)
    except AuthenticationError:
        raise
    except Exception as exc:
        raise AuthenticationError() from exc


def login(*, email: str, password: str) -> AuthResponse:
    """Authenticate with Supabase and return only user and session information."""
    try:
        auth_response = get_supabase_client().auth.sign_in_with_password(
            {"email": email, "password": password}
        )
        return _to_auth_response(auth_response)
    except AuthenticationError:
        raise
    except Exception as exc:
        raise AuthenticationError() from exc
