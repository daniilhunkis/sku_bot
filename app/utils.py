from __future__ import annotations

def fmt_money(v: float | int | None) -> str:
    if v is None:
        return "—"
    return f"{v:,.2f} ₽".replace(",", " ")

def fmt_pct(v: float | int | None) -> str:
    if v is None:
        return "—"
    return f"{v:.2f}%"
