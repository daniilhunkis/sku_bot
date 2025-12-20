from __future__ import annotations
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from app.repo import Repo
from app.config import Config

class InjectMiddleware(BaseMiddleware):
    def __init__(self, repo: Repo, config: Config):
        self.repo = repo
        self.config = config

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        data["repo"] = self.repo
        data["config"] = self.config
        return await handler(event, data)
