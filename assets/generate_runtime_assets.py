"""Create tiny project-local Ursina runtime assets when a Python install lacks them."""
from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'textures'


def _png(width=64, height=64):
    """A crisp neon cog icon rendered as portable RGB PNG bytes."""
    raw = bytearray()
    cx, cy = (width - 1) / 2, (height - 1) / 2
    for y in range(height):
        raw.append(0)
        for x in range(width):
            dx, dy = x - cx, y - cy
            radius = math.hypot(dx, dy)
            angle = math.atan2(dy, dx)
            tooth = 22 + (3 if int((angle + math.pi) / (math.pi / 4)) % 2 == 0 else 0)
            if 10 < radius < tooth:
                pixel = (244, 76, 190)
            elif radius <= 10:
                pixel = (18, 12, 32)
            else:
                pixel = (12, 10, 24)
            raw.extend(pixel)

    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xFFFFFFFF)

    header = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', header) + chunk(b'IDAT', zlib.compress(bytes(raw), 9)) + chunk(b'IEND', b'')


def _ico(png):
    """Windows ICO wrapping the same PNG; supported by modern Panda3D/Windows."""
    return struct.pack('<HHH', 0, 1, 1) + struct.pack('<BBBBHHII', 64, 64, 0, 0, 1, 32, len(png), 22) + png


def ensure_runtime_assets():
    DEST.mkdir(parents=True, exist_ok=True)
    png = _png()
    assets = {
        DEST / 'cog.png': png,
        DEST / 'rune_mommy.ico': _ico(png),
    }
    created = []
    for path, content in assets.items():
        if not path.exists():
            path.write_bytes(content)
            created.append(path.name)
    return created


if __name__ == '__main__':
    print('created:', ', '.join(ensure_runtime_assets()) or '(already present)')
