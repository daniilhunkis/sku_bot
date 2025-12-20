from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

def _csv_ints(s: str) -> list[int]:
    out = []
    for part in (s or "").split(","):
        part = part.strip()
        if not part:
            continue
        out.append(int(part))
    return out

@dataclass(frozen=True)
class Config:
    bot_token: str
    admin_ids: list[int]
    db_dsn: str
    yookassa_shop_id: str | None
    yookassa_secret_key: str | None
    base_currency: str = "RUB"
    log_level: str = "INFO"

def load_config() -> Config:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN is required")
    db_dsn = os.getenv("DB_DSN", "").strip()
    if not db_dsn:
        raise RuntimeError("DB_DSN is required")
    admin_ids = _csv_ints(os.getenv("ADMIN_IDS", ""))
    if not admin_ids:
        raise RuntimeError("ADMIN_IDS is required (comma-separated Telegram user IDs)")
    return Config(
        bot_token=token,
        admin_ids=admin_ids,
        db_dsn=db_dsn,
        yookassa_shop_id=os.getenv("YOOKASSA_SHOP_ID") or None,
        yookassa_secret_key=os.getenv("YOOKASSA_SECRET_KEY") or None,
        base_currency=os.getenv("BASE_CURRENCY", "RUB"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
