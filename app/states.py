from __future__ import annotations
from aiogram.fsm.state import StatesGroup, State


class CalcFlow(StatesGroup):
    choosing_mp = State()
    choosing_scheme = State()
    entering_label = State()       # <— НОВОЕ
    entering_value = State()
    choosing_commission_mode = State()
    choosing_ads_mode = State()
    choosing_tax_mode = State()
    entering_custom_tax = State()
    confirm = State()

class BroadcastFlow(StatesGroup):
    choosing_segment = State()
    waiting_csv = State()
    waiting_text = State()
    waiting_media = State()
    preview = State()

class AdminCreditsFlow(StatesGroup):
    """FSM для админского начисления бесплатных SKU."""
    self_amount = State()
    user_id = State()
    user_amount = State()
