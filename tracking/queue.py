from __future__ import annotations

import asyncio
import logging

log = logging.getLogger("replay.tracking")


class BatchQueue:
    """Buffers events in memory and flushes them to a sink on a timer.

    Used for high-volume, low-value-per-event data (messages, reactions)
    where committing to SQLite on every single event would be wasteful.
    Voice sessions aren't queued here since they're already low-volume
    and each one needs to hit the DB the moment it closes.
    """

    def __init__(self, flush_fn, interval_seconds: float = 5.0, max_buffer: int = 500):
        self._buffer: list = []
        self._flush_fn = flush_fn
        self._interval = interval_seconds
        self._max_buffer = max_buffer
        self._lock = asyncio.Lock()
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
        await self.flush()

    def push(self, item) -> None:
        self._buffer.append(item)
        if len(self._buffer) >= self._max_buffer:
            asyncio.create_task(self.flush())

    async def flush(self) -> None:
        async with self._lock:
            if not self._buffer:
                return
            batch, self._buffer = self._buffer, []
        try:
            await self._flush_fn(batch)
        except Exception:
            log.exception("flush failed, %d events dropped", len(batch))

    async def _loop(self) -> None:
        try:
            while True:
                await asyncio.sleep(self._interval)
                await self.flush()
        except asyncio.CancelledError:
            pass
