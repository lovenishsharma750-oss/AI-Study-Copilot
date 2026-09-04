"""Email/password authentication endpoints."""

from fastapi import APIRouter, HTTPException, status

from app.schemas.auth import AuthResponse, LoginRequest, SignupRequest
from app.services.auth import AuthenticationError, login, signup


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup_route(payload: SignupRequest) -> AuthResponse:
    """Create a Supabase Auth account and its public user profile."""
    try:
        return signup(name=payload.name, email=payload.email, password=payload.password)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to create an account with these details.",
        ) from exc


@router.post("/login", response_model=AuthResponse)
def login_route(payload: LoginRequest) -> AuthResponse:
    """Sign in with Supabase email/password authentication."""
    try:
        return login(email=payload.email, password=payload.password)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        ) from exc
