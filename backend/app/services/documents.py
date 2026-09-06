"""Storage and metadata operations for documents in owned subject workspaces."""

from collections.abc import Mapping
from pathlib import PurePath
import re
from typing import Any
from uuid import uuid4

from app.schemas.document import DocumentResponse
from app.services.supabase import get_authenticated_supabase_client


STUDY_MATERIALS_BUCKET = "study-materials"
_SUPPORTED_MIME_TYPES = {
    ".pdf": "application/pdf",
    ".ppt": "application/vnd.ms-powerpoint",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


class DocumentServiceError(Exception):
    """Raised when a document operation cannot be completed safely."""


class DocumentValidationError(DocumentServiceError):
    """Raised when an uploaded file is not accepted by the MVP upload rules."""


class SubjectNotFoundError(DocumentServiceError):
    """Raised when the requested subject is absent or not owned by the user."""


def _document_response(record: Mapping[str, Any]) -> DocumentResponse:
    return DocumentResponse.model_validate(record)


def _first_document(data: list[dict[str, Any]] | None) -> DocumentResponse | None:
    if not data:
        return None
    return _document_response(data[0])


def _safe_filename(filename: str | None) -> tuple[str, str]:
    """Normalize a client filename and return it with its allowed MIME type."""
    supplied_name = (filename or "").replace("\\", "/")
    basename = PurePath(supplied_name).name.strip()
    cleaned_name = re.sub(r"[^A-Za-z0-9._ -]", "_", basename).strip(" .")
    if not cleaned_name or len(cleaned_name) > 255:
        raise DocumentValidationError()

    extension = PurePath(cleaned_name).suffix.lower()
    mime_type = _SUPPORTED_MIME_TYPES.get(extension)
    if mime_type is None:
        raise DocumentValidationError()
    return cleaned_name, mime_type


def _owned_subject_client(*, user_id: str, access_token: str, subject_id: str) -> Any:
    client = get_authenticated_supabase_client(access_token)
    response = (
        client.table("subjects")
        .select("id")
        .eq("id", subject_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not response.data:
        raise SubjectNotFoundError()
    return client


def upload_document(
    *,
    user_id: str,
    access_token: str,
    subject_id: str,
    filename: str | None,
    content: bytes,
) -> DocumentResponse:
    """Upload an allowed file, then persist its metadata after Storage succeeds."""
    safe_filename, mime_type = _safe_filename(filename)
    if not content:
        raise DocumentValidationError()

    try:
        client = _owned_subject_client(
            user_id=user_id, access_token=access_token, subject_id=subject_id
        )
        document_id = str(uuid4())
        storage_path = f"{user_id}/{subject_id}/{document_id}/{safe_filename}"
        bucket = client.storage.from_(STUDY_MATERIALS_BUCKET)
        bucket.upload(storage_path, content, {"content-type": mime_type})

        try:
            response = (
                client.table("documents")
                .insert(
                    {
                        "id": document_id,
                        "subject_id": subject_id,
                        "file_name": safe_filename,
                        "storage_path": storage_path,
                        "mime_type": mime_type,
                    }
                )
                .execute()
            )
            document = _first_document(response.data)
            if document is None:
                raise ValueError("Document insert returned no record")
            return document
        except Exception:
            try:
                bucket.remove([storage_path])
            except Exception:
                pass
            raise
    except DocumentServiceError:
        raise
    except Exception as exc:
        raise DocumentServiceError() from exc


def list_documents(
    *, user_id: str, access_token: str, subject_id: str
) -> list[DocumentResponse]:
    """List metadata only for documents in an owned subject."""
    try:
        client = _owned_subject_client(
            user_id=user_id, access_token=access_token, subject_id=subject_id
        )
        response = (
            client.table("documents")
            .select("id,subject_id,file_name,storage_path,mime_type,created_at")
            .eq("subject_id", subject_id)
            .order("created_at")
            .execute()
        )
        return [_document_response(record) for record in response.data]
    except DocumentServiceError:
        raise
    except Exception as exc:
        raise DocumentServiceError() from exc


def get_document(
    *, user_id: str, access_token: str, subject_id: str, document_id: str
) -> DocumentResponse | None:
    """Return owned document metadata or None when the document is unavailable."""
    try:
        client = _owned_subject_client(
            user_id=user_id, access_token=access_token, subject_id=subject_id
        )
        response = (
            client.table("documents")
            .select("id,subject_id,file_name,storage_path,mime_type,created_at")
            .eq("id", document_id)
            .eq("subject_id", subject_id)
            .execute()
        )
        return _first_document(response.data)
    except DocumentServiceError:
        raise
    except Exception as exc:
        raise DocumentServiceError() from exc


def delete_document(
    *, user_id: str, access_token: str, subject_id: str, document_id: str
) -> bool:
    """Remove the storage object before deleting its owned metadata row."""
    try:
        client = _owned_subject_client(
            user_id=user_id, access_token=access_token, subject_id=subject_id
        )
        response = (
            client.table("documents")
            .select("id,storage_path")
            .eq("id", document_id)
            .eq("subject_id", subject_id)
            .execute()
        )
        if not response.data:
            return False

        storage_path = response.data[0]["storage_path"]
        client.storage.from_(STUDY_MATERIALS_BUCKET).remove([storage_path])
        deleted = (
            client.table("documents")
            .delete()
            .eq("id", document_id)
            .eq("subject_id", subject_id)
            .execute()
        )
        return bool(deleted.data)
    except DocumentServiceError:
        raise
    except Exception as exc:
        raise DocumentServiceError() from exc
