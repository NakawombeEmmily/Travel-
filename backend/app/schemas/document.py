from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_id: Optional[UUID] = None
    visa_id: Optional[UUID] = None
    original_filename: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    is_encrypted: bool
    checksum: Optional[str] = None
    uploaded_at: datetime


class DocumentListResponse(BaseModel):
    items: list[DocumentRead]
    total: int
