from __future__ import annotations

import io
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_user,
    get_encryption_service,
    get_session,
)
from app.core.security.encryption import EncryptionService
from app.models.user import User
from app.schemas.document import DocumentListResponse, DocumentRead
from app.services.audit import record_audit
from app.services.document import DocumentNotFoundError, DocumentService
from app.services.storage import get_storage

router = APIRouter(prefix="/documents", tags=["documents"])


def _service(
    session: AsyncSession, encryption: EncryptionService
) -> DocumentService:
    return DocumentService(session, encryption, get_storage())


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    client_id: UUID | None = None,
    visa_id: UUID | None = None,
    session: AsyncSession = Depends(get_session),
    encryption: EncryptionService = Depends(get_encryption_service),
    user: User = Depends(get_current_user),
) -> DocumentListResponse:
    items = await _service(session, encryption).list(
        client_id=client_id, visa_id=visa_id
    )
    return DocumentListResponse(
        items=[DocumentRead.model_validate(d) for d in items], total=len(items)
    )


@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    client_id: UUID | None = Form(default=None),
    visa_id: UUID | None = Form(default=None),
    session: AsyncSession = Depends(get_session),
    encryption: EncryptionService = Depends(get_encryption_service),
    user: User = Depends(get_current_user),
) -> DocumentRead:
    if client_id is None and visa_id is None:
        raise HTTPException(
            status_code=400,
            detail="Provide client_id and/or visa_id for the document",
        )
    data = await file.read()
    service = _service(session, encryption)
    document = await service.upload(
        data=data,
        filename=file.filename or "upload",
        content_type=file.content_type,
        client_id=client_id,
        visa_id=visa_id,
        actor_id=user.id,
    )
    await record_audit(
        session,
        action="upload",
        entity_type="document",
        actor_id=user.id,
        entity_id=document.id,
        metadata={"filename": document.original_filename},
    )
    await session.commit()
    return DocumentRead.model_validate(document)


@router.get("/{document_id}/download")
async def download_document(
    document_id: UUID,
    session: AsyncSession = Depends(get_session),
    encryption: EncryptionService = Depends(get_encryption_service),
    user: User = Depends(get_current_user),
) -> StreamingResponse:
    service = _service(session, encryption)
    try:
        document, data = await service.read(document_id)
    except DocumentNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")
    await record_audit(
        session,
        action="download",
        entity_type="document",
        actor_id=user.id,
        entity_id=document_id,
    )
    await session.commit()
    return StreamingResponse(
        io.BytesIO(data),
        media_type=document.file_type or "application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{document.original_filename}"'
        },
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    session: AsyncSession = Depends(get_session),
    encryption: EncryptionService = Depends(get_encryption_service),
    user: User = Depends(get_current_user),
) -> None:
    service = _service(session, encryption)
    try:
        await service.delete(document_id)
    except DocumentNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")
    await record_audit(
        session,
        action="delete",
        entity_type="document",
        actor_id=user.id,
        entity_id=document_id,
    )
    await session.commit()
