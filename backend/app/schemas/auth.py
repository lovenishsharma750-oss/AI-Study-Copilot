"""Request and response schemas for email/password authentication."""

from typing import Annotated

from pydantic import BaseModel, StringConstraints


Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Email = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=3,
        max_length=320,
        pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$",
    ),
]
Password = Annotated[str, StringConstraints(min_length=8, max_length=128)]


class SignupRequest(BaseModel):
    """Credentials and profile name required to create an account."""

    name: Name
    email: Email
    password: Password


class LoginRequest(BaseModel):
    """Credentials required to create a Supabase session."""

    email: Email
    password: Password


class AuthUserResponse(BaseModel):
    """Non-sensitive identifying information for the signed-in user."""

    id: str
    email: str | None = None


class SessionResponse(BaseModel):
    """Session values the frontend needs to authenticate future API calls."""

    access_token: str
    refresh_token: str
    expires_at: int | None = None
    expires_in: int | None = None
    token_type: str | None = None


class AuthResponse(BaseModel):
    """Safe response returned after signup or login."""

    user: AuthUserResponse
    session: SessionResponse | None = None
