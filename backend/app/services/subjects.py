"""Database operations for subjects owned by the authenticated user."""

from collections.abc import Mapping
from typing import Any

from app.schemas.subject import SubjectResponse
from app.services.supabase import get_authenticated_supabase_client


class SubjectServiceError(Exception):
    """Raised when a subject operation cannot be completed safely."""


def _subject_response(record: Mapping[str, Any]) -> SubjectResponse:
    return SubjectResponse.model_validate(record)


def _first_subject(data: list[dict[str, Any]] | None) -> SubjectResponse | None:
    if not data:
        return None
    return _subject_response(data[0])


def create_subject(*, user_id: str, access_token: str, name: str) -> SubjectResponse:
    """Create a subject bound to the currently authenticated user."""
    try:
        response = (
            get_authenticated_supabase_client(access_token)
            .table("subjects")
            .insert({"user_id": user_id, "name": name})
            .execute()
        )
        subject = _first_subject(response.data)
        if subject is None:
            raise ValueError("Subject insert returned no record")
        return subject
    except SubjectServiceError:
        raise
    except Exception as exc:
        raise SubjectServiceError() from exc


def list_subjects(*, user_id: str, access_token: str) -> list[SubjectResponse]:
    """List only the authenticated user's subjects."""
    try:
        response = (
            get_authenticated_supabase_client(access_token)
            .table("subjects")
            .select("id,name,created_at")
            .eq("user_id", user_id)
            .order("created_at")
            .execute()
        )
        return [_subject_response(record) for record in response.data]
    except Exception as exc:
        raise SubjectServiceError() from exc


def get_subject(*, user_id: str, access_token: str, subject_id: str) -> SubjectResponse | None:
    """Return one owned subject, or None when it is absent or belongs to another user."""
    try:
        response = (
            get_authenticated_supabase_client(access_token)
            .table("subjects")
            .select("id,name,created_at")
            .eq("id", subject_id)
            .eq("user_id", user_id)
            .execute()
        )
        return _first_subject(response.data)
    except Exception as exc:
        raise SubjectServiceError() from exc


def update_subject(
    *, user_id: str, access_token: str, subject_id: str, name: str
) -> SubjectResponse | None:
    """Update one owned subject, without permitting ownership changes."""
    try:
        response = (
            get_authenticated_supabase_client(access_token)
            .table("subjects")
            .update({"name": name})
            .eq("id", subject_id)
            .eq("user_id", user_id)
            .execute()
        )
        return _first_subject(response.data)
    except Exception as exc:
        raise SubjectServiceError() from exc


def delete_subject(*, user_id: str, access_token: str, subject_id: str) -> bool:
    """Delete one owned subject and report whether a row was deleted."""
    try:
        response = (
            get_authenticated_supabase_client(access_token)
            .table("subjects")
            .delete()
            .eq("id", subject_id)
            .eq("user_id", user_id)
            .execute()
        )
        return bool(response.data)
    except Exception as exc:
        raise SubjectServiceError() from exc
