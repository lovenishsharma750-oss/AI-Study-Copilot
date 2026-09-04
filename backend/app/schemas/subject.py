"""Request and response schemas for student subjects."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, StringConstraints


SubjectName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]


class SubjectCreateRequest(BaseModel):
    """The minimal data required to create a subject workspace."""

    name: SubjectName


class SubjectUpdateRequest(BaseModel):
    """The editable subject data."""

    name: SubjectName


class SubjectResponse(BaseModel):
    """A subject owned by the authenticated student."""

    id: str
    name: str
    created_at: datetime
