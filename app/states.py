from __future__ import annotations
from aiogram.fsm.state import StatesGroup, State


class CalcFlow(StatesGroup):
    choosing_mp = State()           # 1. Выбор маркетплейса
    choosing_scheme = State()       # 2. Выбор схемы
    entering_label = State()        # 3. Ввод названия
    entering_value = State()        # 4. Ввод значений
    confirm = State()               # 5. Результат

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
