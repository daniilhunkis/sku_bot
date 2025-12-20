from __future__ import annotations

from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def build_pdf(
    title: str,
    subtitle: str,
    inputs_summary: list[tuple[str, str]],
    results_summary: list[tuple[str, str]],
    accuracy: str,
    accuracy_notes: list[str],
    options: list[str],
) -> bytes:
    """
    Строим простой читаемый отчёт в одну-две страницы А4.
    Каждый блок — отдельный раздел.
    """
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    y = height - 40

    # Заголовок
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y, title)
    y -= 24

    c.setFont("Helvetica", 12)
    c.drawString(40, y, subtitle)
    y -= 32

    def draw_section(header: str, lines: list[str]):
        nonlocal y
        if not lines:
            return
        if y < 80:
            c.showPage()
            y = height - 40

        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, header)
        y -= 18

        c.setFont("Helvetica", 10)
        for line in lines:
            if y < 40:
                c.showPage()
                y = height - 40
                c.setFont("Helvetica-Bold", 12)
                c.drawString(40, y, header)
                y -= 18
                c.setFont("Helvetica", 10)
            c.drawString(50, y, f"• {line}")
            y -= 14

        y -= 6

    draw_section("Вводные по SKU", [f"{k}: {v}" for k, v in inputs_summary])
    draw_section("Итоги по 1 продаже", [f"{k}: {v}" for k, v in results_summary])

    acc_lines = [accuracy] + (accuracy_notes or [])
    draw_section("Точность и комментарии", acc_lines)

    draw_section("Варианты действий", options or [])

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.getvalue()
