"""Load shops.json and portrait files for the Ursina desktop game.

Does not write shops.json. Keeps every stall in the file (the ten Clermont
shake shops plus anything Coder added). game.py can `from loaders import ...`.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
PORTRAITS_DIR = ROOT / "client" / "portraits"

# Fallback map if the folder is incomplete. Keys are NPC ids / first names.
PORTRAIT_EXPR = {
    "mira": {
        "smile": "mira-coffee.jpg",
        "wink": "mira-dinner.jpg",
        "lean": "mira-gown.jpg",
        "heat": "mira-lookback.jpg",
        "blush": "mira-stairs.jpg",
        "tease": "mira-courtyard.jpg",
        "default": "mira-coffee.jpg",
    },
    "shake_bar": {
        "default": "mira-coffee.jpg",
        "smile": "mira-coffee.jpg",
    },
    "lila": {
        "smile": "lila-yoga.jpg",
        "default": "lila-yoga.jpg",
    },
}


def load_shops(path: Path | None = None) -> dict:
    """Return the shops.json object as-is. Never drop entries."""
    p = path or (DATA / "shops.json")
    data = json.loads(p.read_text(encoding="utf-8"))
    shops = data.get("shops") or []
    if len(shops) < 10:
        raise RuntimeError(f"shops.json expected at least {10} stalls, got {len(shops)}")
    return data


def shop_list(data: dict | None = None) -> list[dict]:
    data = data if data is not None else load_shops()
    return list(data.get("shops") or [])


def shop_by_id(shop_id: str, data: dict | None = None) -> dict | None:
    for s in shop_list(data):
        if s.get("id") == shop_id:
            return s
    return None


def portrait_path(filename: str) -> Path:
    return PORTRAITS_DIR / filename


def list_portraits() -> list[Path]:
    if not PORTRAITS_DIR.is_dir():
        return []
    return sorted(p for p in PORTRAITS_DIR.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"})


def portraits_for(who: str) -> dict[str, Path]:
    """NPC id or short name -> {expr: absolute Path} for files that exist."""
    key = (who or "").lower()
    pack = PORTRAIT_EXPR.get(key) or {}
    out = {}
    for expr, name in pack.items():
        p = portrait_path(name)
        if p.is_file():
            out[expr] = p
    if not out:
        # fuzzy: any file starting with the name
        for p in list_portraits():
            if p.name.lower().startswith(key):
                out.setdefault("default", p)
    return out


def portrait_texture_path(who: str, expr: str = "default") -> Path | None:
    pack = portraits_for(who)
    return pack.get(expr) or pack.get("default")
