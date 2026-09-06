"""Authenticated document upload and metadata endpoints."""

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status

from app.api.dependencies import CurrentUser, get_current_user
from app.schemas.document import DocumentResponse
from app.services.documents import (
    DocumentServiceError,
    DocumentValidationError,
    SubjectNotFoundError,
    delete_document,
    get_document,
    list_documents,
    upload_document,
)


router = APIRouter(prefix="/api/subjects/{subject_id}/documents", tags=["documents"])


def _service_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Unable to process the document request.",
    )


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject or document not found.")


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document_route(
    subject_id: str,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
) -> DocumentResponse:
    content = await file.read()
    try:
        return upload_document(
            user_id=current_user.id,
            access_token=current_user.access_token,
            subject_id=subject_id,
            filename=file.filename,
            content=content,
        )
    except DocumentValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Upload a non-empty PDF, PPT, PPTX, or DOCX file.",
        ) from exc
    except SubjectNotFoundError as exc:
        raise _not_found() from exc
    except DocumentServiceError as exc:
        raise _service_error() from exc
    finally:
        await file.close()


@router.get("", response_model=list[DocumentResponse])
def list_documents_route(
    subject_id: str, current_user: CurrentUser = Depends(get_current_user)
) -> list[DocumentResponse]:
    try:
        return list_documents(
            user_id=current_user.id,
            access_token=current_user.access_token,
            subject_id=subject_id,
        )
    except SubjectNotFoundError as exc:
        raise _not_found() from exc
    except DocumentServiceError as exc:
        raise _service_error() from exc


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document_route(
    subject_id: str, document_id: str, current_user: CurrentUser = Depends(get_current_user)
) -> DocumentResponse:
    try:
        document = get_document(
            user_id=current_user.id,
            access_token=current_user.access_token,
            subject_id=subject_id,
            document_id=document_id,
        )
    except SubjectNotFoundError as exc:
        raise _not_found() from exc
    except DocumentServiceError as exc:
        raise _service_error() from exc

    if document is None:
        raise _not_found()
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document_route(
    subject_id: str, document_id: str, current_user: CurrentUser = Depends(get_current_user)
) -> Response:
    try:
        deleted = delete_document(
            user_id=current_user.id,
            access_token=current_user.access_token,
            subject_id=subject_id,
            document_id=document_id,
        )
    except SubjectNotFoundError as exc:
        raise _not_found() from exc
    except DocumentServiceError as exc:
        raise _service_error() from exc

    if not deleted:
        raise _not_found()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
