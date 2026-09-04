"""Reusable dependencies for endpoints that require a Supabase user."""

from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.services.supabase import get_supabase_client


_bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    """Authenticated user identity and token for a single request."""

    id: str
    access_token: str


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> CurrentUser:
    """Validate a Supabase bearer token and return its authenticated user."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required.",
        )

    try:
        user_response = get_supabase_client().auth.get_user(credentials.credentials)
        user = getattr(user_response, "user", None)
        if user is None or not getattr(user, "id", None):
            raise ValueError("Supabase did not return an authenticated user")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
        ) from exc

    return CurrentUser(id=str(user.id), access_token=credentials.credentials)
