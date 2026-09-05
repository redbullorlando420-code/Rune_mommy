#!/usr/bin/env python3
"""Rune Mommy entry. Reassembles split source then runs (GitHub push size workaround)."""
from __future__ import annotations
from pathlib import Path

_ROOT = Path(__file__).resolve().parent

# Decode/write ground textures before stitch (zip often lacks binary jpgs).
try:
    import sys as _sys
    if str(_ROOT) not in _sys.path:
        _sys.path.insert(0, str(_ROOT))
    from assets.generate_textures import ensure_all as _ensure_textures
    _ensure_textures()
except Exception as _tex_exc:
    print("[textures] fallback skip:", _tex_exc)

_parts = sorted((_ROOT / "_game_parts").glob("part*.py.txt"))
if not _parts:
    raise SystemExit("missing _game_parts/part*.py.txt")
_src = "".join(p.read_text(encoding="utf-8") for p in _parts)
_ns = {"__name__": "__main__", "__file__": str(_ROOT / "game.py")}
exec(compile(_src, str(_ROOT / "game.py"), "exec"), _ns, _ns)
