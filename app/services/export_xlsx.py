from datetime import datetime
from io import BytesIO
from typing import Iterable

from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font


def _normalize_cell_value(value):
    # Excel не любит tz-aware datetime, убираем tzinfo
    if isinstance(value, datetime) and value.tzinfo is not None:
        return value.replace(tzinfo=None)
    return value


def build_admin_export(users_rows: Iterable[dict], payments_rows: Iterable[dict]) -> bytes:
    wb = Workbook()

    # --- Users sheet ---
    ws_users = wb.active
    ws_users.title = "Users"

    user_headers = [
        "id",
        "tg_user_id",
        "created_at",
        "started_at",
        "last_seen_at",
        "free_credits",
        "paid_credits",
        "used_credits",
    ]
    ws_users.append(user_headers)
    for cell in ws_users[1]:
        cell.font = Font(bold=True)

    for r in users_rows:
        ws_users.append([_normalize_cell_value(r.get(h)) for h in user_headers])

    # --- Payments sheet ---
    ws_payments = wb.create_sheet("Payments")

    payment_headers = [
        "id",
        "user_id",
        "created_at",
        "amount_rub",
        "credits",
        "provider",
        "external_id",
        "raw",
    ]
    ws_payments.append(payment_headers)
    for cell in ws_payments[1]:
        cell.font = Font(bold=True)

    for r in payments_rows:
        ws_payments.append([_normalize_cell_value(r.get(h)) for h in payment_headers])

    # Автоширина колонок
    for ws in (ws_users, ws_payments):
        for column_cells in ws.columns:
            length = max(
                len(str(cell.value)) if cell.value is not None else 0
                for cell in column_cells
            )
            ws.column_dimensions[get_column_letter(column_cells[0].column)].width = max(
                10, length + 2
            )

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()
