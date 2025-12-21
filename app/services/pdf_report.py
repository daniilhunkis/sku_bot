from __future__ import annotations

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# Регистрируем шрифт с поддержкой русского
def _setup_fonts():
    """Настройка шрифтов для поддержки русского текста"""
    try:
        # Пробуем найти и зарегистрировать шрифт DejaVu
        possible_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
            "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf",
            "/home/sku_bot/sku_profit_bot/app/fonts/DejaVuSans.ttf",  # Добавил локальный путь
        ]
        
        font_path = None
        for path in possible_paths:
            if os.path.exists(path):
                font_path = path
                break
        
        if font_path:
            # Регистрируем обычный и жирный шрифты
            pdfmetrics.registerFont(TTFont('DejaVu', font_path))
            pdfmetrics.registerFont(TTFont('DejaVu-Bold', font_path))
            return 'DejaVu'
    except Exception as e:
        print(f"Warning: Could not register DejaVu font: {e}")
    
    # Fallback на стандартные шрифты
    print("Using fallback fonts (Helvetica)")
    return 'Helvetica'


def build_pdf(
    title: str,
    subtitle: str,
    inputs_summary: list[tuple[str, str]],
    results_summary: list[tuple[str, str]],
    accuracy: str,
    accuracy_notes: list[str],
    options: list[str],
    sku_name: str = None,  # Добавил параметр для названия SKU
) -> bytes:
    """
    Строим простой читаемый отчёт в одну-две страницы А4.
    Каждый блок — отдельный раздел.
    """
    # Настраиваем шрифты
    font_name = _setup_fonts()
    
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    y = height - 40

    # ЗАГОЛОВОК С НАЗВАНИЕМ РАСЧЕТА
    if sku_name:
        c.setFont(f"{font_name}-Bold", 16)
        title_with_sku = f"Отчёт по SKU: {sku_name}"
        c.drawCentredString(width / 2, y, title_with_sku)
        y -= 20
    
    # Основной заголовок
    c.setFont(f"{font_name}-Bold", 14)
    c.drawCentredString(width / 2, y, title)
    y -= 24

    if subtitle:
        c.setFont(font_name, 12)
        c.drawCentredString(width / 2, y, subtitle)
        y -= 32

    def draw_section(header: str, lines: list[tuple[str, str]]):
        nonlocal y
        if not lines:
            return
        if y < 80:
            c.showPage()
            y = height - 40
            c.setFont(font_name, 10)

	    # Убираем эмодзи из заголовков или заменяем на текст
    	    header_clean = header
    	    emoji_replacements = {
        	"📋": "[Данные]",
        	"💰": "[Результаты]", 
        	"🎯": "[Точность]",
        	"💡": "[Рекомендации]"
    	    }

        c.setFont(f"{font_name}-Bold", 12)
        c.drawString(40, y, header)
        y -= 20

        c.setFont(font_name, 10)
        for key, value in lines:
            if y < 50:
                c.showPage()
                y = height - 40
                c.setFont(font_name, 10)
            
            # Форматируем текст
            if value is None:
                value = ""
            elif isinstance(value, (int, float)):
                value = str(value)
            
            text = f"• {key}: {value}"
            
            # Разбиваем слишком длинные строки
            max_length = 80
            if len(text) > max_length:
                # Разбиваем по словам
                words = text.split()
                lines_text = []
                current_line = ""
                
                for word in words:
                    if len(current_line) + len(word) + 1 <= max_length:
                        if current_line:
                            current_line += " " + word
                        else:
                            current_line = word
                    else:
                        lines_text.append(current_line)
                        current_line = "  " + word  # Отступ для продолжения
                
                if current_line:
                    lines_text.append(current_line)
                
                for i, line in enumerate(lines_text):
                    if y < 50:
                        c.showPage()
                        y = height - 40
                        c.setFont(font_name, 10)
                    c.drawString(50, y, line)
                    y -= 14
            else:
                c.drawString(50, y, text)
                y -= 14

        y -= 6

    # Вводные данные
    draw_section("📋 Вводные данные", inputs_summary)
    
    # Результаты
    draw_section("💰 Результаты расчёта", results_summary)
    
    # Точность
    c.setFont(f"{font_name}-Bold", 12)
    c.drawString(40, y, "🎯 Точность расчёта")
    y -= 20
    
    c.setFont(font_name, 10)
    # Разбиваем accuracy на строки если нужно
    if len(accuracy) > 80:
        words = accuracy.split()
        current_line = ""
        for word in words:
            if len(current_line) + len(word) + 1 <= 80:
                if current_line:
                    current_line += " " + word
                else:
                    current_line = word
            else:
                c.drawString(50, y, current_line)
                y -= 14
                current_line = word
        if current_line:
            c.drawString(50, y, current_line)
            y -= 14
    else:
        c.drawString(50, y, accuracy)
        y -= 14
    
    y -= 6
    
    # Комментарии по точности
    if accuracy_notes:
        c.setFont(f"{font_name}-Bold", 10)
        c.drawString(40, y, "Примечания:")
        y -= 15
        
        c.setFont(font_name, 9)
        for note in accuracy_notes:
            if y < 50:
                c.showPage()
                y = height - 40
                c.setFont(font_name, 9)
            
            # Очищаем HTML и другие символы
            note_clean = note.replace("<b>", "").replace("</b>", "")
            c.drawString(50, y, f"• {note_clean}")
            y -= 12
        
        y -= 6
    
    # Рекомендации
    if options:
        c.setFont(f"{font_name}-Bold", 12)
        c.drawString(40, y, "💡 Рекомендации")
        y -= 20
        
        c.setFont(font_name, 10)
        for option in options[:5]:  # Ограничиваем 5 рекомендациями
            if y < 50:
                c.showPage()
                y = height - 40
                c.setFont(font_name, 10)
            
            # Очищаем HTML-теги из опций
            option_clean = option.replace("<b>", "").replace("</b>", "")
            option_clean = option_clean.replace("&nbsp;", " ")
            
            # Разбиваем длинные рекомендации
            words = option_clean.split()
            lines_text = []
            current_line = ""
            
            for word in words:
                if len(current_line) + len(word) + 1 <= 80:
                    if current_line:
                        current_line += " " + word
                    else:
                        current_line = "• " + word
                else:
                    lines_text.append(current_line)
                    current_line = "  " + word  # Отступ для продолжения
            
            if current_line:
                lines_text.append(current_line)
            
            for line in lines_text:
                if y < 50:
                    c.showPage()
                    y = height - 40
                    c.setFont(font_name, 10)
                c.drawString(50, y, line)
                y -= 14
            
            y -= 5  # Отступ между рекомендациями

    c.save()
    buf.seek(0)
    return buf.getvalue()
