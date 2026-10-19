from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AdminLedgerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    crm_payment_id: UUID
    client_id: Optional[UUID] = None
    trip_id: Optional[UUID] = None
    amount: Decimal
    currency: str
    status: str
    provider: Optional[str] = None
    provider_transaction_id: Optional[str] = None
    invoice_number: Optional[str] = None
    synced_at: datetime
    last_reconciled_at: Optional[datetime] = None
