#!/usr/bin/env python3
"""Rune Mommy entry. Reassembles split source then runs (GitHub push size workaround)."""
from __future__ import annotations
from pathlib import Path
_ROOT = Path(__file__).resolve().parent
_parts = sorted((_ROOT / "_game_parts").glob("part*.py.txt"))
if not _parts:
    raise SystemExit("missing _game_parts/part*.py.txt — pull latest main")
_code = "".join(p.read_text(encoding="utf-8") for p in _parts)
_g = {"__name__": "__main__", "__file__": str(_ROOT / "game_full.py")}
exec(compile(_code, str(_ROOT / "game_full.py"), "exec"), _g)
