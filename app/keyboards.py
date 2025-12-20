from __future__ import annotations

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

from app.constants import MARKETPLACES, SCHEMES_BY_MP, PACKS


def main_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="▶️ Рассчитать SKU", callback_data="calc:start")
    kb.button(text="📁 Мои расчёты", callback_data="calc:history:0")
    kb.button(text="ℹ️ Как считается", callback_data="help:how")
    kb.adjust(1)
    return kb.as_markup()


def marketplaces_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for code, name in MARKETPLACES:
        kb.button(text=name, callback_data=f"calc:mp:{code}")
    kb.adjust(2, 2, 2)
    return kb.as_markup()


def schemes_kb(mp_code: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for code, name in SCHEMES_BY_MP.get(mp_code, []):
        kb.button(text=name, callback_data=f"calc:scheme:{code}")
    kb.button(text="◀️ Назад", callback_data="calc:back:mp")
    kb.adjust(3, 1)
    return kb.as_markup()


def yes_no_kb(yes_cb: str, no_cb: str,
              yes_text: str = "✅ Да",
              no_text: str = "❌ Нет") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=yes_text, callback_data=yes_cb)
    kb.button(text=no_text, callback_data=no_cb)
    kb.adjust(2)
    return kb.as_markup()


def input_help_kb(field: str,
                  allow_default: bool = True,
                  allow_zero: bool = True) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✍️ Ввести", callback_data=f"calc:enter:{field}")
    if allow_default:
        kb.button(
            text="🤷 Не знаю → типовое",
            callback_data=f"calc:default:{field}",
        )
    if allow_zero:
        kb.button(
            text="0️⃣ Не учитывать",
            callback_data=f"calc:zero:{field}",
        )
    kb.button(text="◀️ Назад", callback_data="calc:back:field")
    kb.adjust(1)
    return kb.as_markup()


def commission_mode_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="% от цены", callback_data="calc:commode:PCT")
    kb.button(text="₽ фикс", callback_data="calc:commode:RUB")
    kb.button(text="◀️ Назад", callback_data="calc:back:field")
    kb.adjust(2, 1)
    return kb.as_markup()


def ads_mode_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="₽ на 1 продажу",
              callback_data="calc:adsmode:PER_SALE")
    kb.button(text="ДРР (%)", callback_data="calc:adsmode:DRR")
    kb.button(text="◀️ Назад", callback_data="calc:back:field")
    kb.adjust(2, 1)
    return kb.as_markup()


def tax_mode_kb() -> InlineKeyboardMarkup:
    """
    Два режима:
    • Налог с выручки (доходов)
    • Налог с прибыли (доходы минус расходы)
    """
    kb = InlineKeyboardBuilder()
    kb.button(
        text="С дохода (с выручки)",
        callback_data="calc:tax:REV",
    )
    kb.button(
        text="С дохода минус расходы",
        callback_data="calc:tax:PROFIT",
    )
    kb.button(text="◀️ Назад", callback_data="calc:back:field")
    kb.adjust(1)
    return kb.as_markup()


def packs_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for credits, price in PACKS:
        kb.button(
            text=f"{credits} SKU — {price}₽",
            callback_data=f"buy:pack:{credits}:{price}",
        )
    kb.button(text="◀️ Назад", callback_data="buy:back")
    kb.adjust(2, 2, 1)
    return kb.as_markup()


def result_kb(calc_id: int | None = None) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="💾 Сохранить", callback_data="calc:save")
    kb.button(text="📄 Скачать PDF (A4)", callback_data="calc:pdf")
    kb.button(text="🔁 Начать расчёт заново", callback_data="calc:start")
    kb.button(text="➕ Рассчитать ещё SKU", callback_data="calc:start")
    kb.button(text="🏠 Главное меню", callback_data="menu")
    kb.adjust(2, 2, 1)
    return kb.as_markup()


def result_saved_kb(calc_id: int) -> InlineKeyboardMarkup:
    """
    Клавиатура для расчёта, открытого из истории.
    """
    kb = InlineKeyboardBuilder()
    kb.button(text="📄 Скачать PDF (A4)", callback_data="calc:pdf")
    kb.button(
        text="🗑 Удалить из сохранённых",
        callback_data=f"calc:delete:{calc_id}",
    )
    kb.button(text="🏠 Главное меню", callback_data="menu")
    kb.button(
        text="⬅️ К списку расчётов",
        callback_data="calc:history:0",
    )
    kb.adjust(1)
    return kb.as_markup()


def history_nav_kb(offset: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    prev_off = max(0, offset - 20)
    next_off = offset + 20
    kb.button(text="◀️", callback_data=f"calc:history:{prev_off}")
    kb.button(text="▶️", callback_data=f"calc:history:{next_off}")
    kb.button(text="🏠 Меню", callback_data="menu")
    kb.adjust(3)
    return kb.as_markup()


def admin_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📊 Статистика", callback_data="admin:stats")
    kb.button(text="⬇️ Экспорт XLSX", callback_data="admin:export")
    kb.button(text="📣 Рассылка", callback_data="admin:broadcast:start")
    kb.button(text="➕ Начислить себе SKU", callback_data="admin:credits:self")
    kb.button(
        text="🎁 Начислить пользователю SKU",
        callback_data="admin:credits:user",
    )
    kb.adjust(1)
    return kb.as_markup()


def admin_broadcast_segment_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Все пользователи", callback_data="admin:broadcast:seg:all")
    kb.button(
        text="Есть бесплатные",
        callback_data="admin:broadcast:seg:free_remaining",
    )
    kb.button(
        text="Бесплатные закончились",
        callback_data="admin:broadcast:seg:free_finished",
    )
    kb.button(text="Покупатели", callback_data="admin:broadcast:seg:buyers")
    kb.button(
        text="CSV со списком user_id",
        callback_data="admin:broadcast:seg:csv",
    )
    kb.button(text="Отмена", callback_data="admin:broadcast:cancel")
    kb.adjust(1)
    return kb.as_markup()


def admin_broadcast_media_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="Пропустить медиа",
        callback_data="admin:broadcast:media:skip",
    )
    kb.button(text="Отмена", callback_data="admin:broadcast:cancel")
    kb.adjust(1)
    return kb.as_markup()


def admin_broadcast_confirm_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="✅ Запустить рассылку",
        callback_data="admin:broadcast:confirm",
    )
    kb.button(text="❌ Отмена", callback_data="admin:broadcast:cancel")
    kb.adjust(1)
    return kb.as_markup()
