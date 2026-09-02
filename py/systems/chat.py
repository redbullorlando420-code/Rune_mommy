"""Chat + commands. Port of server/systems/chat.js."""
from __future__ import annotations

import re

from constants import CHANNELS, LOCAL_CHAT_RANGE, MAX_CHAT, dist, now

RATE_MS = 350
_CTRL = re.compile(r"[\x00-\x1f]")


def handle_chat(world, player, channel, text):
    if not isinstance(text, str):
        return
    text = _CTRL.sub("", text).strip()[:MAX_CHAT]
    if not text:
        return
    t = now()
    if t - (player.lastChat or 0) < RATE_MS:
        return
    player.lastChat = t
    if text.startswith("/"):
        return command(world, player, text)
    ch = CHANNELS["LOCAL"] if channel == CHANNELS["LOCAL"] else CHANNELS["GLOBAL"]
    msg = {"t": "chat", "p": {"from": player.name, "id": player.id, "channel": ch, "text": text, "ts": t}}
    if ch == CHANNELS["LOCAL"]:
        for o in world.players.values():
            if dist(player, o) <= LOCAL_CHAT_RANGE:
                world.to(o, msg)
    else:
        world.broadcast(msg)


def command(world, player, text):
    parts = text[1:].split()
    if not parts:
        return
    cmd = parts[0]
    arg = " ".join(parts[1:])
    if cmd in ("who", "players"):
        names = ", ".join(p.name for p in world.players.values())
        system(world, player, f"Wanderers: {names}")
    elif cmd == "help":
        system(world, player, "Click ground to walk. Click shops, trees, beasts, players. I pack, T trade. /who /w Name text /emote")
    elif cmd in ("emote", "me"):
        world.broadcast({
            "t": "chat",
            "p": {
                "from": player.name, "id": player.id, "channel": CHANNELS["GLOBAL"],
                "text": f"* {player.name} {arg} *", "ts": now(), "emote": True,
            },
        })
    elif cmd in ("w", "whisper", "tell"):
        sp = arg.find(" ")
        if sp < 1:
            system(world, player, "Usage: /w Name hello")
            return
        target_name = arg[:sp]
        body = arg[sp + 1:].strip()
        if not body:
            return
        other = None
        for o in world.players.values():
            if o.name.lower() == target_name.lower():
                other = o
                break
        if not other:
            system(world, player, "No wanderer by that name.")
            return
        msg = {
            "t": "chat",
            "p": {
                "from": player.name, "id": player.id, "channel": "whisper",
                "text": body, "ts": now(), "to": other.name,
            },
        }
        world.to(player, msg)
        world.to(other, msg)
    else:
        system(world, player, "Unknown command. Try /help")


def system(world, player, text):
    world.to(player, {"t": "chat", "p": {"from": "Hollow", "id": "sys", "channel": CHANNELS["SYSTEM"], "text": text, "ts": now()}})


def announce(world, text):
    world.broadcast({"t": "chat", "p": {"from": "Hollow", "id": "sys", "channel": CHANNELS["SYSTEM"], "text": text, "ts": now()}})
