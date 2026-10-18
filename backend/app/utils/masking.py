from datetime import date
from dateutil.relativedelta import relativedelta


def mask_passport(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 4:
        return "*" * len(value)
    return "*" * (len(value) - 4) + value[-4:]


def passport_expiring_soon(expiry: date | None, within_months: int = 6) -> bool:
    if expiry is None:
        return False
    return expiry <= date.today() + relativedelta(months=within_months)
