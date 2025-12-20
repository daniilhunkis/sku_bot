from __future__ import annotations
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from app.config import Config
from app.repo import Repo
from app.keyboards import packs_kb, main_menu_kb, yes_no_kb
from app.services.payments import YooKassaClient

router = Router()

@router.callback_query(F.data == "buy:back")
async def buy_back(cb: CallbackQuery):
    await cb.message.edit_text("Меню:", reply_markup=main_menu_kb())

@router.callback_query(F.data.startswith("buy:pack:"))
async def buy_pack(cb: CallbackQuery, repo: Repo, config: Config, state: FSMContext):
    parts = cb.data.split(":")
    credits = int(parts[-2])
    price = int(parts[-1])

    if not (config.yookassa_shop_id and config.yookassa_secret_key):
        await cb.answer("YooKassa не настроена. Добавьте YOOKASSA_SHOP_ID и YOOKASSA_SECRET_KEY в .env", show_alert=True)
        return

    client = YooKassaClient(config.yookassa_shop_id, config.yookassa_secret_key)
    return_url = "https://t.me/"  # not used by bot, required by YooKassa; can be any
    desc = f"Пакет {credits} SKU"
    pay = client.create_payment(price, desc, return_url)

    # store pending in FSM to check later
    await state.update_data(pending_payment_id=pay.payment_id, pending_pack_credits=credits, pending_pack_price=price)
    await repo.create_payment_record(
        cb.from_user.id, provider="yookassa", provider_payment_id=pay.payment_id,
        status="PENDING", pack_credits=credits, amount_rub=price, raw={"confirmation_url": pay.confirmation_url}
    )

    text = (
        f"Оплата пакета: {credits} SKU за {price} ₽\n\n"
        f"1) Откройте ссылку и оплатите\n"
        f"2) Вернитесь сюда и нажмите «✅ Я оплатил»\n\n"
        f"Ссылка оплаты: {pay.confirmation_url}"
    )
    await cb.message.edit_text(text, reply_markup=yes_no_kb("buy:check", "menu", yes_text="✅ Я оплатил", no_text="🏠 В меню"))

@router.callback_query(F.data == "buy:check")
async def buy_check(cb: CallbackQuery, repo: Repo, config: Config, state: FSMContext):
    data = await state.get_data()
    pay_id = data.get("pending_payment_id")
    credits = data.get("pending_pack_credits")
    price = data.get("pending_pack_price")
    if not pay_id:
        await cb.answer("Нет ожидаемой оплаты.", show_alert=True)
        return

    client = YooKassaClient(config.yookassa_shop_id, config.yookassa_secret_key)
    status = client.get_status(pay_id)

    if status == "succeeded":
        await repo.update_payment_status(pay_id, "SUCCEEDED", {"status": status})
        await repo.add_paid_credits(cb.from_user.id, int(credits))
        await state.update_data(pending_payment_id=None, pending_pack_credits=None, pending_pack_price=None)
        u = await repo.get_user(cb.from_user.id)
        await cb.message.edit_text(
            f"✅ Оплата подтверждена! Начислено {credits} SKU.\n"
            f"Доступно: бесплатных {u['free_credits']}, платных {u['paid_credits']}.",
            reply_markup=main_menu_kb()
        )
        return

    if status in ("pending", "waiting_for_capture"):
        await cb.answer("Пока не вижу успешной оплаты. Попробуйте ещё раз через минуту.", show_alert=True)
        return

    # canceled/failed
    await repo.update_payment_status(pay_id, status.upper(), {"status": status})
    await state.update_data(pending_payment_id=None, pending_pack_credits=None, pending_pack_price=None)
    await cb.message.edit_text("Оплата не прошла или отменена. Можете попробовать снова:", reply_markup=packs_kb())
