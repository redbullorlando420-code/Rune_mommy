#!/usr/bin/env python3
"""Decode assets/tex_b64/*.b64 into assets/textures/*.jpg (GitHub text-push workaround)."""
from __future__ import annotations
from pathlib import Path
import base64
import sys

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "tex_b64"
DEST = ROOT / "textures"

def ensure() -> list[str]:
    DEST.mkdir(parents=True, exist_ok=True)
    written = []
    if not SRC.is_dir():
        return written
    for b64p in sorted(SRC.glob("*.b64")):
        name = b64p.stem + ".jpg"
        out = DEST / name
        raw = "".join(b64p.read_text(encoding="utf-8").split())
        data = base64.b64decode(raw)
        if out.exists() and out.stat().st_size == len(data):
            continue
        out.write_bytes(data)
        written.append(name)
    return written

def install() -> list[str]:
    return ensure()

if __name__ == "__main__":
    w = ensure()
    print("wrote:", ", ".join(w) if w else "(already present)")
    sys.exit(0)
