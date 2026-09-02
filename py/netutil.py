"""Shared websocket send helper (async fire-and-forget)."""
from __future__ import annotations

import asyncio


def ws_open(ws):
    if ws is None:
        return False
    state = getattr(ws, "state", None)
    if state is None:
        return True
    name = getattr(state, "name", str(state))
    return name.endswith("OPEN") or name == "OPEN"


def send_ws(ws, data):
    if not ws_open(ws):
        return
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return
    loop.create_task(_safe_send(ws, data))


async def _safe_send(ws, data):
    try:
        await ws.send(data)
    except Exception:
        pass
