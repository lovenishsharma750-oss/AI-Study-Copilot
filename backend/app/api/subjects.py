"""Authenticated subject workspace endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.dependencies import CurrentUser, get_current_user
from app.schemas.subject import SubjectCreateRequest, SubjectResponse, SubjectUpdateRequest
from app.services.subjects import (
    SubjectServiceError,
    create_subject,
    delete_subject,
    get_subject,
    list_subjects,
    update_subject,
)


router = APIRouter(prefix="/api/subjects", tags=["subjects"])


def _service_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Unable to process the subject request.",
    )


@router.post("", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
def create_subject_route(
    payload: SubjectCreateRequest, current_user: CurrentUser = Depends(get_current_user)
) -> SubjectResponse:
    try:
        return create_subject(
            user_id=current_user.id, access_token=current_user.access_token, name=payload.name
        )
    except SubjectServiceError as exc:
        raise _service_error() from exc


@router.get("", response_model=list[SubjectResponse])
def list_subjects_route(
    current_user: CurrentUser = Depends(get_current_user),
) -> list[SubjectResponse]:
    try:
        return list_subjects(user_id=current_user.id, access_token=current_user.access_token)
    except SubjectServiceError as exc:
        raise _service_error() from exc


@router.get("/{subject_id}", response_model=SubjectResponse)
def get_subject_route(
    subject_id: str, current_user: CurrentUser = Depends(get_current_user)
) -> SubjectResponse:
    try:
        subject = get_subject(
            user_id=current_user.id,
            access_token=current_user.access_token,
            subject_id=subject_id,
        )
    except SubjectServiceError as exc:
        raise _service_error() from exc

    if subject is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found.")
    return subject


@router.patch("/{subject_id}", response_model=SubjectResponse)
def update_subject_route(
    subject_id: str,
    payload: SubjectUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> SubjectResponse:
    try:
        subject = update_subject(
            user_id=current_user.id,
            access_token=current_user.access_token,
            subject_id=subject_id,
            name=payload.name,
        )
    except SubjectServiceError as exc:
        raise _service_error() from exc

    if subject is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found.")
    return subject


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject_route(
    subject_id: str, current_user: CurrentUser = Depends(get_current_user)
) -> Response:
    try:
        deleted = delete_subject(
            user_id=current_user.id,
            access_token=current_user.access_token,
            subject_id=subject_id,
        )
    except SubjectServiceError as exc:
        raise _service_error() from exc

    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
