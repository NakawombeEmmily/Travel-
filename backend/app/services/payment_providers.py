from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
import uuid

from app.core.config import settings


class PaymentProviderError(Exception):
    """Raised when a payment provider cannot process a request."""


@dataclass
class PaymentResult:
    success: bool
    status: str
    provider_transaction_id: str | None = None
    message: str | None = None
    raw: dict = field(default_factory=dict)


class PaymentProvider(ABC):
    """Interface every payment integration must implement."""

    name: str = "base"

    @abstractmethod
    def charge(
        self,
        *,
        amount: Decimal,
        currency: str,
        method: str,
        reference: str,
        metadata: dict | None = None,
    ) -> PaymentResult:
        raise NotImplementedError

    @abstractmethod
    def refund(
        self,
        *,
        provider_transaction_id: str,
        amount: Decimal,
        currency: str,
    ) -> PaymentResult:
        raise NotImplementedError


class MockPaymentProvider(PaymentProvider):
    """Deterministic provider used for local development and tests."""

    name = "mock"

    def charge(
        self,
        *,
        amount: Decimal,
        currency: str,
        method: str,
        reference: str,
        metadata: dict | None = None,
    ) -> PaymentResult:
        return PaymentResult(
            success=True,
            status="completed",
            provider_transaction_id=f"mock_{uuid.uuid4().hex}",
            message="Mock charge approved",
            raw={"reference": reference, "amount": str(amount), "currency": currency},
        )

    def refund(
        self,
        *,
        provider_transaction_id: str,
        amount: Decimal,
        currency: str,
    ) -> PaymentResult:
        return PaymentResult(
            success=True,
            status="refunded",
            provider_transaction_id=f"mockref_{uuid.uuid4().hex}",
            message="Mock refund approved",
            raw={"original": provider_transaction_id, "amount": str(amount)},
        )


class _UnconfiguredProvider(PaymentProvider):
    """Stub for real providers that are not yet configured."""

    def charge(self, *, amount, currency, method, reference, metadata=None):
        raise PaymentProviderError(
            f"{self.name} provider is not configured yet"
        )

    def refund(self, *, provider_transaction_id, amount, currency):
        raise PaymentProviderError(
            f"{self.name} provider is not configured yet"
        )


class FlutterwaveProvider(_UnconfiguredProvider):
    name = "flutterwave"


class StripeProvider(_UnconfiguredProvider):
    name = "stripe"


class MTNMoMoProvider(_UnconfiguredProvider):
    name = "mtn"


class AirtelMoneyProvider(_UnconfiguredProvider):
    name = "airtel"


_PROVIDERS: dict[str, type[PaymentProvider]] = {
    MockPaymentProvider.name: MockPaymentProvider,
    FlutterwaveProvider.name: FlutterwaveProvider,
    StripeProvider.name: StripeProvider,
    MTNMoMoProvider.name: MTNMoMoProvider,
    AirtelMoneyProvider.name: AirtelMoneyProvider,
}


def get_payment_provider(name: str | None = None) -> PaymentProvider:
    key = (name or settings.PAYMENT_PROVIDER or "mock").lower()
    provider_cls = _PROVIDERS.get(key)
    if provider_cls is None:
        raise PaymentProviderError(f"Unknown payment provider: {key}")
    return provider_cls()
