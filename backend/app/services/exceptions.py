from __future__ import annotations


class ClientNotFoundError(Exception):
    """Raised when a referenced client does not exist or is soft-deleted."""


class NotFoundError(Exception):
    """Raised when a referenced resource does not exist."""


class ConflictError(Exception):
    """Raised when a unique constraint would be violated."""


class PaymentError(Exception):
    """Raised when a payment cannot be processed as requested."""
