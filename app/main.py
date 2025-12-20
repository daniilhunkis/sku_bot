from __future__ import annotations
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties  # <-- ВАЖНЫЙ импорт

from app.config import load_config
from app.db import Database
from app.repo import Repo
from app.middlewares import InjectMiddleware
from app.handlers import user, admin, buy


async def main():
    config = load_config()
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper(), logging.INFO)
    )

    db = Database(config.db_dsn)
    await db.connect()
    repo = Repo(db)

    # ИСПРАВЛЕНО: убрали parse_mode=..., используем default=DefaultBotProperties(...)
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher(storage=MemoryStorage())
    dp.message.middleware(InjectMiddleware(repo, config))
    dp.callback_query.middleware(InjectMiddleware(repo, config))

    dp.include_router(admin.router)
    dp.include_router(buy.router)
    dp.include_router(user.router)

    try:
        await dp.start_polling(bot)
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
