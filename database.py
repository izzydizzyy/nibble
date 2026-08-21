import asyncio
import time
from collections import defaultdict
from contextlib import asynccontextmanager

import aiosqlite

import config

_db: aiosqlite.Connection | None = None
_user_locks: dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id         INTEGER PRIMARY KEY,
    balance         INTEGER NOT NULL DEFAULT 0,
    rod_tier        INTEGER NOT NULL DEFAULT 1,
    last_daily      REAL,
    daily_streak    INTEGER NOT NULL DEFAULT 0,
    last_fish       REAL,
    total_fish      INTEGER NOT NULL DEFAULT 0,
    created_at      REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS inventory (
    user_id     INTEGER NOT NULL,
    fish_id     INTEGER NOT NULL,
    quantity    INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, fish_id)
);

CREATE TABLE IF NOT EXISTS trades (
    trade_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    user_a          INTEGER NOT NULL,
    user_b          INTEGER NOT NULL,
    offer_a_fish    INTEGER,
    offer_a_qty     INTEGER,
    offer_b_fish    INTEGER,
    offer_b_qty     INTEGER,
    confirmed_a     INTEGER NOT NULL DEFAULT 0,
    confirmed_b     INTEGER NOT NULL DEFAULT 0,
    status          TEXT NOT NULL DEFAULT 'pending',
    created_at      REAL NOT NULL
);
"""


def user_lock(user_id: int) -> asyncio.Lock:
    return _user_locks[user_id]


async def init_db():
    global _db
    _db = await aiosqlite.connect(config.DATABASE_PATH)
    _db.row_factory = aiosqlite.Row
    await _db.executescript(SCHEMA)
    await _db.commit()


async def close_db():
    if _db:
        await _db.close()


@asynccontextmanager
async def tx():

    try:
        yield _db
        await _db.commit()
    except Exception:
        await _db.rollback()
        raise


async def ensure_user(user_id: int):
    await _db.execute(
        "INSERT OR IGNORE INTO users (user_id, created_at) VALUES (?, ?)",
        (user_id, time.time()),
    )
    await _db.commit()


async def get_user(user_id: int) -> aiosqlite.Row:
    await ensure_user(user_id)
    async with _db.execute(
        "SELECT * FROM users WHERE user_id = ?", (user_id,)
    ) as cur:
        return await cur.fetchone()


async def add_balance(user_id: int, amount: int):
    await ensure_user(user_id)
    await _db.execute(
        "UPDATE users SET balance = balance + ? WHERE user_id = ?",
        (amount, user_id),
    )
    await _db.commit()


async def set_balance(user_id: int, amount: int):
    await ensure_user(user_id)
    await _db.execute(
        "UPDATE users SET balance = ? WHERE user_id = ?", (amount, user_id)
    )
    await _db.commit()


async def try_spend(user_id: int, amount: int) -> bool:

    await ensure_user(user_id)
    cur = await _db.execute(
        "UPDATE users SET balance = balance - ? "
        "WHERE user_id = ? AND balance >= ?",
        (amount, user_id, amount),
    )
    await _db.commit()
    return cur.rowcount > 0


async def set_last_fish(user_id: int, ts: float):
    await _db.execute(
        "UPDATE users SET last_fish = ?, total_fish = total_fish + 1 "
        "WHERE user_id = ?",
        (ts, user_id),
    )
    await _db.commit()


async def set_daily(user_id: int, ts: float, streak: int):
    await _db.execute(
        "UPDATE users SET last_daily = ?, daily_streak = ? WHERE user_id = ?",
        (ts, streak, user_id),
    )
    await _db.commit()


async def set_rod_tier(user_id: int, tier: int):
    await _db.execute(
        "UPDATE users SET rod_tier = ? WHERE user_id = ?", (tier, user_id)
    )
    await _db.commit()


async def add_fish(user_id: int, fish_id: int, qty: int = 1):
    await _db.execute(
        "INSERT INTO inventory (user_id, fish_id, quantity) VALUES (?, ?, ?) "
        "ON CONFLICT(user_id, fish_id) DO UPDATE SET quantity = quantity + ?",
        (user_id, fish_id, qty, qty),
    )
    await _db.commit()


async def remove_fish(user_id: int, fish_id: int, qty: int) -> bool:

    cur = await _db.execute(
        "UPDATE inventory SET quantity = quantity - ? "
        "WHERE user_id = ? AND fish_id = ? AND quantity >= ?",
        (qty, user_id, fish_id, qty),
    )
    await _db.commit()
    return cur.rowcount > 0


async def get_inventory(user_id: int) -> list[aiosqlite.Row]:
    async with _db.execute(
        "SELECT fish_id, quantity FROM inventory "
        "WHERE user_id = ? AND quantity > 0 ORDER BY fish_id",
        (user_id,),
    ) as cur:
        return await cur.fetchall()


async def get_fish_qty(user_id: int, fish_id: int) -> int:
    async with _db.execute(
        "SELECT quantity FROM inventory WHERE user_id = ? AND fish_id = ?",
        (user_id, fish_id),
    ) as cur:
        row = await cur.fetchone()
        return row["quantity"] if row else 0


async def leaderboard_balance(limit: int = 10) -> list[aiosqlite.Row]:
    async with _db.execute(
        "SELECT user_id, balance FROM users ORDER BY balance DESC LIMIT ?",
        (limit,),
    ) as cur:
        return await cur.fetchall()


async def leaderboard_collection(limit: int = 10) -> list[aiosqlite.Row]:
    async with _db.execute(
        "SELECT user_id, COUNT(DISTINCT fish_id) AS unique_fish "
        "FROM inventory WHERE quantity > 0 "
        "GROUP BY user_id ORDER BY unique_fish DESC LIMIT ?",
        (limit,),
    ) as cur:
        return await cur.fetchall()
