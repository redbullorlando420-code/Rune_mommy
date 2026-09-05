#!/usr/bin/env python3
"""Monolith mirror for editors. Runtime entry is game.py (stitches _game_parts).
Rebuild locally:
  python -c "from pathlib import Path; p=Path('_game_parts'); Path('game.full.py').write_text(''.join(x.read_text(encoding='utf-8') for x in sorted(p.glob('part*.py.txt'))), encoding='utf-8')"
"""
raise SystemExit("Use: py -3 game.py  (stitches _game_parts). Or rebuild this file from parts — see docstring.")
