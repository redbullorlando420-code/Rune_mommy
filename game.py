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

# Ursina 8 can omit its optional editor cog/icon from some Python builds.
# Keep equivalents in this project so the game is runnable and self-contained.
try:
    from assets.generate_runtime_assets import ensure_runtime_assets as _ensure_runtime_assets
    _ensure_runtime_assets()
except Exception as _runtime_assets_exc:
    print("[runtime assets] fallback skip:", _runtime_assets_exc)

_parts = sorted((_ROOT / "_game_parts").glob("part*.py.txt"))
if not _parts:
    raise SystemExit("missing _game_parts/part*.py.txt")
_src = "".join(p.read_text(encoding="utf-8") for p in _parts)
# Ursina discovers global ``update`` and ``input`` callbacks from the actual
# ``__main__`` module.  Executing into a private dictionary lets the title
# buttons render, but leaves keyboard events and per-frame movement invisible
# to the engine.  Assemble directly into this module's globals instead.
_runtime_globals = globals()
_runtime_globals["__file__"] = str(_ROOT / "game.py")
exec(compile(_src, str(_ROOT / "game.py"), "exec"), _runtime_globals, _runtime_globals)
