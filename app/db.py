from __future__ import annotations
import asyncpg
from typing import Any

CREATE_SQL = [
    """CREATE TABLE IF NOT EXISTS users (
        id BIGSERIAL PRIMARY KEY,
        tg_user_id BIGINT UNIQUE NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        last_seen TIMESTAMPTZ NOT NULL DEFAULT now(),
        free_credits INT NOT NULL DEFAULT 2,
        paid_credits INT NOT NULL DEFAULT 0,
        started_count INT NOT NULL DEFAULT 0
    );""",
    """CREATE TABLE IF NOT EXISTS calculations (
        id BIGSERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        marketplace TEXT NOT NULL,
        scheme TEXT NOT NULL,
        sku_label TEXT,
        inputs JSONB NOT NULL,
        results JSONB NOT NULL,
        accuracy_level TEXT NOT NULL,
        used_credit_type TEXT NOT NULL
    );""",
    """CREATE TABLE IF NOT EXISTS payments (
        id BIGSERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        provider TEXT NOT NULL,
        provider_payment_id TEXT UNIQUE NOT NULL,
        status TEXT NOT NULL,
        pack_sku_credits INT NOT NULL,
        amount_rub INT NOT NULL,
        raw JSONB NOT NULL
    );""",
    """CREATE TABLE IF NOT EXISTS reference_values (
        id BIGSERIAL PRIMARY KEY,
        marketplace TEXT NOT NULL,
        scheme TEXT,
        key TEXT NOT NULL,
        value NUMERIC NOT NULL,
        unit TEXT NOT NULL,
        source_title TEXT,
        source_url TEXT,
        source_date DATE,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        UNIQUE(marketplace, scheme, key)
    );""",
]

class Database:
    def __init__(self, dsn: str):
        self._dsn = dsn
        self.pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        self.pool = await asyncpg.create_pool(self._dsn, min_size=1, max_size=10)
        async with self.pool.acquire() as conn:
            for sql in CREATE_SQL:
                await conn.execute(sql)

    async def close(self) -> None:
        if self.pool:
            await self.pool.close()

    async def fetchrow(self, sql: str, *args) -> asyncpg.Record | None:
        assert self.pool
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(sql, *args)

    async def fetch(self, sql: str, *args) -> list[asyncpg.Record]:
        assert self.pool
        async with self.pool.acquire() as conn:
            return await conn.fetch(sql, *args)

    async def execute(self, sql: str, *args) -> str:
        assert self.pool
        async with self.pool.acquire() as conn:
            return await conn.execute(sql, *args)

    async def executemany(self, sql: str, args_list: list[tuple[Any, ...]]) -> None:
        assert self.pool
        async with self.pool.acquire() as conn:
            await conn.executemany(sql, args_list)
