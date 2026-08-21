from __future__ import annotations

import logging
from pathlib import Path

import aiosqlite

from database.schema import DDL, SCHEMA_VERSION

log = logging.getLogger("replay.database")


class Database:
    """Thin wrapper around a single aiosqlite connection.

    SQLite handles one writer at a time regardless of how many
    connections you open, so we keep exactly one connection and rely
    on aiosqlite's internal write lock rather than a connection pool.
    WAL mode lets reads proceed while a write is in flight.
    """

    def __init__(self, path: Path):
        self._path = path
        self._conn: aiosqlite.Connection | None = None

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Database.connect() must be called before use")
        return self._conn

    async def connect(self) -> None:
        self._conn = await aiosqlite.connect(self._path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode = WAL")
        await self._conn.execute("PRAGMA foreign_keys = ON")
        await self._conn.execute("PRAGMA synchronous = NORMAL")
        await self._migrate()
        log.info("ready")

    async def _migrate(self) -> None:
        await self._conn.executescript(DDL)
        cursor = await self._conn.execute("SELECT version FROM schema_meta")
        row = await cursor.fetchone()
        if row is None:
            await self._conn.execute(
                "INSERT INTO schema_meta (version) VALUES (?)", (SCHEMA_VERSION,)
            )
        await self._conn.commit()

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None
