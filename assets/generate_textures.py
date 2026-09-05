#!/usr/bin/env python3
"""Ensure assets/textures/*.jpg exist (decode tex_b64, else procedural PNG fallback)."""
from __future__ import annotations
from pathlib import Path
import struct
import zlib

ROOT = Path(__file__).resolve().parent
DEST = ROOT / "textures"
NAMES = ("grass", "asphalt", "concrete", "brick", "stucco", "water")


def _hash(x: int, y: int, s: int = 0) -> int:
    n = (x * 374761393 + y * 668265263 + s * 982451653) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    return n & 255


def _pixel(name: str, x: int, y: int) -> tuple[int, int, int]:
    if name == "grass":
        return (34 + _hash(x, y, 1) % 40, 90 + _hash(x, y, 2) % 50, 28 + _hash(x, y, 3) % 30)
    if name == "asphalt":
        v = 40 + _hash(x, y, 4) % 25
        return (v, v, min(255, v + _hash(x, y, 5) % 8))
    if name == "concrete":
        v = 150 + _hash(x, y, 6) % 40
        return (v, v, max(0, v - 5))
    if name == "brick":
        return (140 + _hash(x // 8, y // 4, 7) % 40, 50 + _hash(x, y, 8) % 30, 40 + _hash(x, y, 9) % 20)
    if name == "stucco":
        v = 200 + _hash(x, y, 10) % 30
        return (v, max(0, v - 10), max(0, v - 20))
    if name == "water":
        return (30 + _hash(x, y, 11) % 40, 90 + _hash(x, y, 12) % 50, 160 + _hash(x, y, 13) % 60)
    return (128, 128, 128)


def _png(w: int, h: int, name: str) -> bytes:
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        for x in range(w):
            raw.extend(_pixel(name, x, y))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")


def _from_b64() -> list[str]:
    try:
        from assets.install_textures import ensure
        return ensure()
    except Exception:
        return []


def ensure_all() -> list[str]:
    DEST.mkdir(parents=True, exist_ok=True)
    written = list(_from_b64())
    for name in NAMES:
        jpg = DEST / f"{name}.jpg"
        png = DEST / f"{name}.png"
        if jpg.exists() or png.exists():
            continue
        png.write_bytes(_png(64, 64, name))
        written.append(png.name)
    return written


if __name__ == "__main__":
    print("wrote:", ", ".join(ensure_all()) or "(already present)")
