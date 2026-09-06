"""Response schemas for subject documents."""

from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    """Metadata for a study document stored in Supabase Storage."""

    id: str
    subject_id: str
    file_name: str
    storage_path: str
    mime_type: str | None = None
    created_at: datetime
