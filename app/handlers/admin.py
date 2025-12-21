from __future__ import annotations

import csv

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.types import BufferedInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app.config import Config
from app.repo import Repo
from app.keyboards import (
    admin_menu_kb,
    admin_broadcast_segment_kb,
    admin_broadcast_media_kb,
    admin_broadcast_confirm_kb,
)
from app.states import BroadcastFlow, AdminCreditsFlow
from app.services.export_xlsx import build_admin_export

router = Router()


def _is_admin(user_id: int, config: Config) -> bool:
    return user_id in config.admin_ids


# --- вход в админку ---


@router.message(Command("admin"))
async def admin_entry(message: Message, config: Config):
    if not _is_admin(message.from_user.id, config):
        return
    await message.answer("Админ-панель:", reply_markup=admin_menu_kb())


# --- статистика ---


@router.callback_query(F.data == "admin:stats")
async def admin_stats(cb: CallbackQuery, repo: Repo, config: Config):
    if not _is_admin(cb.from_user.id, config):
        return
    s = await repo.admin_stats()
    text = (
        "📊 Статистика\n\n"
        f"• Пользователей в базе: {s['users_total']}\n"
        f"• Пользователей запускали бота: {s['users_started']}\n"
        f"• Всего запусков (/start): {s['starts_total']}\n"
        f"• Всего расчётов: {s['calculations_total']}\n"
        f"• Бесплатных расчётов: {s['free_calculations']}\n"
        f"• Платных расчётов: {s['paid_calculations']}\n\n"
        f"• Покупок: {s['payments_count']}\n"
        f"• Сумма покупок: {s['payments_sum_rub']} ₽\n"
    )
    await cb.message.edit_text(text, reply_markup=admin_menu_kb())


# --- экспорт ---


@router.callback_query(F.data == "admin:export")
async def admin_export(cb: CallbackQuery, repo: Repo, config: Config, bot: Bot):
    if not _is_admin(cb.from_user.id, config):
        return

    try:
        users_rows, payments_rows = await repo.admin_export_rows()
        xlsx_bytes = build_admin_export(users_rows, payments_rows)
        
        if not xlsx_bytes or len(xlsx_bytes) < 100:
            await cb.answer("Ошибка: файл не сгенерирован или слишком мал", show_alert=True)
            return
            
        doc = BufferedInputFile(xlsx_bytes, filename="admin_export.xlsx")
        await bot.send_document(cb.from_user.id, doc)
        await cb.answer("✅ Экспорт отправлен", show_alert=False)
        
    except Exception as e:
        await cb.answer(f"Ошибка экспорта: {str(e)[:50]}", show_alert=True)
        print(f"Export error: {e}")  # Для логов


# --- начисление SKU ---


@router.callback_query(F.data == "admin:credits:self")
async def admin_credits_self_start(
    cb: CallbackQuery, state: FSMContext, config: Config
):
    if not _is_admin(cb.from_user.id, config):
        return
    await state.set_state(AdminCreditsFlow.self_amount)
    await cb.message.edit_text(
        "Сколько бесплатных SKU начислить вам?\n\n"
        "Отправьте целое число, например: 50",
        reply_markup=None,
    )


@router.message(AdminCreditsFlow.self_amount)
async def admin_credits_self_amount(
    message: Message, state: FSMContext, repo: Repo, config: Config
):
    if not _is_admin(message.from_user.id, config):
        return
    try:
        amount = int((message.text or "").strip())
        if amount <= 0:
            raise ValueError
    except Exception:
        await message.answer("Нужно положительное целое число, например: 25")
        return

    await repo.grant_free_credits(message.from_user.id, amount)
    await state.clear()
    await message.answer(
        f"✅ Начислено {amount} бесплатных SKU на ваш аккаунт.",
        reply_markup=admin_menu_kb(),
    )


@router.callback_query(F.data == "admin:credits:user")
async def admin_credits_user_start(
    cb: CallbackQuery, state: FSMContext, config: Config
):
    if not _is_admin(cb.from_user.id, config):
        return
    await state.set_state(AdminCreditsFlow.user_id)
    await cb.message.edit_text(
        "Введите Telegram ID пользователя, которому нужно начислить SKU.\n\n"
        "Пример: 123456789",
        reply_markup=None,
    )


@router.message(AdminCreditsFlow.user_id)
async def admin_credits_user_id(
    message: Message, state: FSMContext, config: Config
):
    if not _is_admin(message.from_user.id, config):
        return
    txt = (message.text or "").strip()
    if not txt.isdigit():
        await message.answer("Нужен числовой user_id. Пример: 123456789")
        return
    await state.update_data(target_user_id=int(txt))
    await state.set_state(AdminCreditsFlow.user_amount)
    await message.answer(
        "Сколько бесплатных SKU начислить этому пользователю?\n\n"
        "Отправьте целое число, например: 100",
        reply_markup=None,
    )


@router.message(AdminCreditsFlow.user_amount)
async def admin_credits_user_amount(
    message: Message, state: FSMContext, repo: Repo, config: Config
):
    if not _is_admin(message.from_user.id, config):
        return
    data = await state.get_data()
    target_id = data.get("target_user_id")
    if not target_id:
        await message.answer("Не вижу целевого user_id, начните заново через админку.")
        await state.clear()
        return
    try:
        amount = int((message.text or "").strip())
        if amount <= 0:
            raise ValueError
    except Exception:
        await message.answer("Нужно положительное целое число, например: 50")
        return

    await repo.grant_free_credits(target_id, amount)
    await state.clear()
    await message.answer(
        f"✅ Начислено {amount} бесплатных SKU пользователю {target_id}.",
        reply_markup=admin_menu_kb(),
    )


# --- рассылка ---


@router.callback_query(F.data == "admin:broadcast:start")
async def bc_start(cb: CallbackQuery, state: FSMContext, config: Config):
    if not _is_admin(cb.from_user.id, config):
        return
    await state.clear()
    await state.set_state(BroadcastFlow.choosing_segment)
    await cb.message.edit_text(
        "Выберите сегмент для рассылки:",
        reply_markup=admin_broadcast_segment_kb(),
    )


@router.callback_query(F.data.startswith("admin:broadcast:seg:"))
async def bc_segment(cb: CallbackQuery, state: FSMContext, repo: Repo, config: Config):
    if not _is_admin(cb.from_user.id, config):
        return
    seg = cb.data.split(":")[-1]
    await state.update_data(
        segment=seg, user_ids=None, text=None, media=None, media_type=None
    )
    if seg == "csv":
        await state.set_state(BroadcastFlow.waiting_csv)
        await cb.message.edit_text(
            "Пришлите CSV файл (одна колонка user_id или tg_user_id).",
            reply_markup=admin_broadcast_segment_kb(),
        )
        return

    user_ids = await repo.list_user_ids(seg)
    await state.update_data(user_ids=user_ids)
    await state.set_state(BroadcastFlow.waiting_text)
    await cb.message.edit_text(
        f"Сегмент выбран. Получателей: {len(user_ids)}\n\n"
        f"Пришлите текст рассылки.",
        reply_markup=None,
    )


@router.message(BroadcastFlow.waiting_csv)
async def bc_csv(message: Message, state: FSMContext, config: Config, bot: Bot):
    if not _is_admin(message.from_user.id, config):
        return
    if not message.document:
        await message.answer("Нужен CSV-файл документом.")
        return
    file = await bot.get_file(message.document.file_id)
    content = await bot.download_file(file.file_path)
    data = content.read()
    user_ids: list[int] = []
    try:
        text = data.decode("utf-8-sig")
        reader = csv.reader(text.splitlines())
        for row in reader:
            if not row:
                continue
            cell = row[0].strip()
            if not cell or not cell.isdigit():
                continue
            user_ids.append(int(cell))
    except Exception:
        await message.answer(
            "Не смог прочитать CSV. Формат: одна колонка с числовыми user_id."
        )
        return

    user_ids = sorted(set(user_ids))
    await state.update_data(user_ids=user_ids, segment="csv")
    await state.set_state(BroadcastFlow.waiting_text)
    await message.answer(
        f"CSV загружен. Получателей: {len(user_ids)}\n\nПришлите текст рассылки."
    )


@router.message(BroadcastFlow.waiting_text)
async def bc_text(message: Message, state: FSMContext, config: Config):
    if not _is_admin(message.from_user.id, config):
        return
    txt = (message.text or "").strip()
    if not txt:
        await message.answer("Текст пустой. Пришлите текст рассылки.")
        return
    await state.update_data(text=txt)
    await state.set_state(BroadcastFlow.waiting_media)
    await message.answer(
        "Теперь пришлите медиа (фото/видео/гиф/файл) "
        "или нажмите «Пропустить».",
        reply_markup=admin_broadcast_media_kb(),
    )


@router.callback_query(F.data == "admin:broadcast:media:skip")
async def bc_media_skip(cb: CallbackQuery, state: FSMContext, config: Config):
    if not _is_admin(cb.from_user.id, config):
        return
    await state.update_data(media=None, media_type=None)
    await _bc_preview(cb.message, state, config)


@router.message(BroadcastFlow.waiting_media)
async def bc_media(message: Message, state: FSMContext, config: Config):
    if not _is_admin(message.from_user.id, config):
        return
    media = None
    media_type = None
    if message.photo:
        media = message.photo[-1].file_id
        media_type = "photo"
    elif message.video:
        media = message.video.file_id
        media_type = "video"
    elif message.animation:
        media = message.animation.file_id
        media_type = "animation"
    elif message.document:
        media = message.document.file_id
        media_type = "document"

    if not media:
        await message.answer(
            "Не вижу медиа. Пришлите фото/видео/гиф/файл "
            "или нажмите «Пропустить»."
        )
        return

    await state.update_data(media=media, media_type=media_type)
    await _bc_preview(message, state, config)


async def _bc_preview(message_or_msg, state: FSMContext, config: Config):
    data = await state.get_data()
    user_ids = data.get("user_ids") or []
    txt = data.get("text") or ""
    media = data.get("media")
    media_type = data.get("media_type")
    await state.set_state(BroadcastFlow.preview)

    await message_or_msg.answer(
        f"👀 Предпросмотр рассылки\n"
        f"Получателей: {len(user_ids)}\n\n"
        f"Текст:\n{txt}"
    )
    if media:
        if media_type == "photo":
            await message_or_msg.answer_photo(media, caption=txt)
        elif media_type == "video":
            await message_or_msg.answer_video(media, caption=txt)
        elif media_type == "animation":
            await message_or_msg.answer_animation(media, caption=txt)
        elif media_type == "document":
            await message_or_msg.answer_document(media, caption=txt)
    await message_or_msg.answer(
        "Подтвердить запуск?",
        reply_markup=admin_broadcast_confirm_kb(),
    )


@router.callback_query(F.data == "admin:broadcast:confirm")
async def bc_confirm(cb: CallbackQuery, state: FSMContext, config: Config, bot: Bot):
    if not _is_admin(cb.from_user.id, config):
        return
    data = await state.get_data()
    user_ids = data.get("user_ids") or []
    txt = data.get("text") or ""
    media = data.get("media")
    media_type = data.get("media_type")
    await cb.message.edit_text(
        f"🚀 Запускаю рассылку… Получателей: {len(user_ids)}"
    )
    await state.clear()

    sent = 0
    failed = 0
    for uid in user_ids:
        try:
            if media:
                if media_type == "photo":
                    await bot.send_photo(uid, media, caption=txt)
                elif media_type == "video":
                    await bot.send_video(uid, media, caption=txt)
                elif media_type == "animation":
                    await bot.send_animation(uid, media, caption=txt)
                elif media_type == "document":
                    await bot.send_document(uid, media, caption=txt)
                else:
                    await bot.send_message(uid, txt)
            else:
                await bot.send_message(uid, txt)
            sent += 1
        except Exception:
            failed += 1
        if (sent + failed) % 50 == 0:
            try:
                await cb.message.answer(
                    f"Прогресс: {sent} отправлено, {failed} ошибок…"
                )
            except Exception:
                pass

    await cb.message.answer(
        f"✅ Рассылка завершена. Отправлено: {sent}, ошибок: {failed}"
    )


@router.callback_query(F.data == "admin:broadcast:cancel")
async def bc_cancel(cb: CallbackQuery, state: FSMContext, config: Config):
    if not _is_admin(cb.from_user.id, config):
        return
    await state.clear()
    await cb.message.edit_text(
        "Рассылка отменена.",
        reply_markup=admin_menu_kb(),
    )
