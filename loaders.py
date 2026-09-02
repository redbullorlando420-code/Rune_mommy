"""Load shops, npcs, items, and per-character portrait folders.

Portrait layout (supplied by Imagine generator):
    client/portraits/<npc>/<expression>.png|.jpg
    client/portraits/_legacy/   old flat names, ignored as a character

Filename stem is the expression (smile, wink, lean, ...).
Dialogue keys look/smirk/tease/rest/blush/heat/care fall back to smile or lean.
Does not write shops.json.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
PORTRAITS_DIR = ROOT / "client" / "portraits"
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}

# dialogue expressions that may not have their own file yet
EXPR_FALLBACK = {
    "look": ("smile", "default"),
    "smirk": ("wink", "smile", "default"),
    "tease": ("lean", "wink", "smile", "default"),
    "rest": ("smile", "default"),
    "blush": ("smile", "lean", "default"),
    "heat": ("lean", "wink", "smile", "default"),
    "care": ("smile", "default"),
    "default": ("smile",),
}

# shop / display-name aliases -> folder name
ALIASES = {
    "shake_bar": "mira",
    "mama mira": "mira",
    "mama_mira": "mira",
    "mira": "mira",
    "gun_hut": "gage",
    "gage": "gage",
    "lila": "lila",
    "rosa": "rosa",
    "yara": "yara",
    "maera": "yara",
}


def load_shops(path: Path | None = None) -> dict:
    """Return shops.json as-is. Never drop entries."""
    p = path or (DATA / "shops.json")
    data = json.loads(p.read_text(encoding="utf-8"))
    shops = data.get("shops") or []
    if len(shops) < 10:
        raise RuntimeError(f"shops.json expected at least 10 stalls, got {len(shops)}")
    return data


def shop_list(data: dict | None = None) -> list[dict]:
    data = data if data is not None else load_shops()
    return list(data.get("shops") or [])


def shop_by_id(shop_id: str, data: dict | None = None) -> dict | None:
    for s in shop_list(data):
        if s.get("id") == shop_id:
            return s
    return None


def load_npcs(path: Path | None = None) -> dict:
    p = path or (DATA / "npcs.json")
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError("npcs.json must be an object keyed by id")
    return data


def load_mobs(path: Path | None = None) -> dict:
    p = path or (DATA / "mobs.json")
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError("mobs.json must be an object keyed by id")
    return data


def load_items(path: Path | None = None) -> dict:
    p = path or (DATA / "items.json")
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError("items.json must be an object keyed by id")
    return data


def _norm(who: str) -> str:
    key = (who or "").strip().lower().replace("-", "_")
    key = " ".join(key.split())
    if key in ALIASES:
        return ALIASES[key]
    # "Mama Mira" -> mira
    last = key.split()[-1] if key else ""
    if last in ALIASES:
        return ALIASES[last]
    return key.replace(" ", "_")


def _scan_folder(folder: Path) -> dict[str, Path]:
    out: dict[str, Path] = {}
    if not folder.is_dir():
        return out
    for p in folder.iterdir():
        if not p.is_file() or p.suffix.lower() not in IMAGE_EXTS:
            continue
        out[p.stem.lower()] = p
    return out


def _legacy_for(who: str) -> dict[str, Path]:
    """Flat leftovers: mira-coffee.jpg, lila-yoga.jpg, or _legacy/ copies."""
    out: dict[str, Path] = {}
    folders = [PORTRAITS_DIR, PORTRAITS_DIR / "_legacy"]
    prefix = who.lower() + "-"
    for folder in folders:
        if not folder.is_dir():
            continue
        for p in folder.iterdir():
            if not p.is_file() or p.suffix.lower() not in IMAGE_EXTS:
                continue
            name = p.name.lower()
            if name.startswith(prefix):
                expr = p.stem.lower()[len(who) + 1 :]
                out.setdefault(expr or "default", p)
            elif p.stem.lower() == who:
                out.setdefault("default", p)
    return out


def portraits_for(who: str) -> dict[str, Path]:
    """NPC id / shop id / display name -> {expression: Path}."""
    key = _norm(who)
    pack = _scan_folder(PORTRAITS_DIR / key)
    for expr, path in _legacy_for(key).items():
        pack.setdefault(expr, path)
    if "default" not in pack:
        for cand in ("smile", "wink", "lean"):
            if cand in pack:
                pack["default"] = pack[cand]
                break
        if "default" not in pack and pack:
            pack["default"] = next(iter(pack.values()))
    # shop portrait field / npc portrait field aliases
    try:
        for shop in shop_list():
            if shop.get("id") == who or shop.get("portrait") == who:
                other = _norm(shop.get("portrait") or shop.get("npcName") or "")
                if other and other != key:
                    for expr, path in portraits_for(other).items():
                        pack.setdefault(expr, path)
    except Exception:
        pass
    return pack


def portrait_texture_path(who: str, expr: str = "default") -> Path | None:
    pack = portraits_for(who)
    if not pack:
        return None
    want = (expr or "default").lower()
    if want in pack:
        return pack[want]
    for fb in EXPR_FALLBACK.get(want, ()):
        if fb in pack:
            return pack[fb]
    return pack.get("default") or pack.get("smile") or next(iter(pack.values()), None)


def list_characters() -> list[str]:
    if not PORTRAITS_DIR.is_dir():
        return []
    names = []
    for p in sorted(PORTRAITS_DIR.iterdir()):
        if p.is_dir() and not p.name.startswith("_") and not p.name.startswith("."):
            names.append(p.name)
    return names


def _read_json(rel: str):
    p = DATA / rel
    if not p.exists():
        p = ROOT / rel
    return json.loads(p.read_text(encoding="utf-8"))


def load_oss_items() -> dict:
    """CC-BY-SA CDDA workshop tools. Does not write shops.json."""
    data = _read_json("oss_items.json")
    items = data.get("items") or {}
    return items if isinstance(items, dict) else {}


def load_vehicles() -> dict:
    """Local park cars plus CDDA bike/moto catalog."""
    local = _read_json("vehicles.json")
    oss = _read_json("oss_vehicles.json")
    return {"local": local, "oss": oss.get("vehicles") or []}


def load_skills() -> dict:
    """Hollow skills plus CDDA skill ids for leveling."""
    hollow = _read_json("skills.json")
    oss = _read_json("oss_skills.json")
    return {"hollow": hollow, "oss": oss}


def load_progression() -> dict:
    return _read_json("progression.json")
