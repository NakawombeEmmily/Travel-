from __future__ import annotations

from datetime import date
from decimal import Decimal

_PAGE_WIDTH = 595
_PAGE_HEIGHT = 842
_MARGIN_X = 50
_TOP_Y = 790
_LINE_HEIGHT = 16
_MAX_LINES = 46

COMPANY_NAME = "Travel System"


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _page_content(lines: list[str]) -> bytes:
    parts = ["BT", "/F1 12 Tf", f"{_LINE_HEIGHT} TL", f"{_MARGIN_X} {_TOP_Y} Td"]
    for line in lines:
        parts.append(f"({_escape(line)}) Tj")
        parts.append("T*")
    parts.append("ET")
    return "\n".join(parts).encode("latin-1", "replace")


def render_simple_pdf(lines: list[str]) -> bytes:
    """Render plain text lines into a minimal, dependency-free PDF document."""
    text_lines = [str(line) for line in lines]
    chunks = [
        text_lines[i : i + _MAX_LINES]
        for i in range(0, len(text_lines), _MAX_LINES)
    ] or [[""]]
    page_count = len(chunks)

    catalog_id = 1
    pages_id = 2
    font_id = 3
    page_ids = [4 + 2 * i for i in range(page_count)]
    content_ids = [5 + 2 * i for i in range(page_count)]

    objects: dict[int, bytes] = {}
    objects[catalog_id] = f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode()
    kids = " ".join(f"{pid} 0 R" for pid in page_ids)
    objects[pages_id] = (
        f"<< /Type /Pages /Kids [{kids}] /Count {page_count} >>".encode()
    )
    objects[font_id] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"

    for index, chunk in enumerate(chunks):
        content = _page_content(chunk)
        objects[page_ids[index]] = (
            f"<< /Type /Page /Parent {pages_id} 0 R "
            f"/MediaBox [0 0 {_PAGE_WIDTH} {_PAGE_HEIGHT}] "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> "
            f"/Contents {content_ids[index]} 0 R >>"
        ).encode()
        objects[content_ids[index]] = (
            b"<< /Length "
            + str(len(content)).encode()
            + b" >>\nstream\n"
            + content
            + b"\nendstream"
        )

    max_id = max(objects)
    out = bytearray(b"%PDF-1.4\n")
    offsets: dict[int, int] = {}
    for obj_id in range(1, max_id + 1):
        obj = objects.get(obj_id)
        if obj is None:
            continue
        offsets[obj_id] = len(out)
        out += f"{obj_id} 0 obj\n".encode() + obj + b"\nendobj\n"

    xref_pos = len(out)
    out += f"xref\n0 {max_id + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for obj_id in range(1, max_id + 1):
        if obj_id in offsets:
            out += f"{offsets[obj_id]:010d} 00000 n \n".encode()
        else:
            out += b"0000000000 65535 f \n"
    out += (
        f"trailer\n<< /Size {max_id + 1} /Root {catalog_id} 0 R >>\n"
        f"startxref\n{xref_pos}\n%%EOF"
    ).encode()
    return bytes(out)


def _money(amount: Decimal | float, currency: str) -> str:
    return f"{currency} {Decimal(str(amount)):,.2f}"


def build_invoice_pdf(
    *,
    invoice_number: str,
    issue_date: date | str,
    due_date: date | str | None,
    client_name: str,
    currency: str,
    amount: Decimal | float,
    status: str,
    client_email: str | None = None,
    items: list[tuple[str, Decimal | float]] | None = None,
    notes: str | None = None,
    title: str = "INVOICE",
) -> bytes:
    lines: list[str] = [
        COMPANY_NAME,
        "",
        f"{title} {invoice_number}",
        f"Issue date: {issue_date}",
    ]
    if due_date:
        lines.append(f"Due date: {due_date}")
    lines.append("")
    lines.append(f"Billed to: {client_name}")
    if client_email:
        lines.append(f"Email: {client_email}")
    lines.append("")
    lines.append("-" * 62)
    lines.append(f"{'Description':<42}{'Amount':>20}")
    lines.append("-" * 62)
    for description, item_amount in items or [("Travel services", amount)]:
        lines.append(f"{str(description)[:40]:<42}{_money(item_amount, currency):>20}")
    lines.append("-" * 62)
    lines.append(f"{'Total':<42}{_money(amount, currency):>20}")
    lines.append("")
    lines.append(f"Status: {status.upper()}")
    if notes:
        lines.append("")
        lines.append(f"Notes: {notes}")
    lines.append("")
    lines.append("Thank you for your business.")
    return render_simple_pdf(lines)


def build_receipt_pdf(
    *,
    receipt_number: str,
    paid_on: date | str,
    client_name: str,
    currency: str,
    amount: Decimal | float,
    status: str,
    client_email: str | None = None,
    notes: str | None = None,
) -> bytes:
    return build_invoice_pdf(
        invoice_number=receipt_number,
        issue_date=paid_on,
        due_date=None,
        client_name=client_name,
        client_email=client_email,
        currency=currency,
        amount=amount,
        status=status,
        notes=notes,
        title="RECEIPT",
    )
