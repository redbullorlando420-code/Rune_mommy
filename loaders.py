"""Load shops.json and portraits for the Ursina desktop game.

Portrait layout (advanced):
    client/portraits/<npc_id>/<expression>.<ext>
    client/portraits/_legacy/<old-flat-name>.<ext>   # old mira-coffee.jpg style

Discovery is folder-first. portraits.json is optional aliases + expression fallbacks.
Does not write shops.json. Keeps every stall in the file.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
PORTRAITS_DIR = ROOT / "client" / "portraits"
MANIFEST_PATH = PORTRAITS_DIR / "portraits.json"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

# Built-in aliases if portraits.json is missing.
_ALIASES = {
    "mira": "mira",
    "mama mira": "mira",
    "mama_mira": "mira",
    "shake_bar": "mira",
    "shakebar": "mira",
    "lila": "lila",
    "michelle": "michelle",
    "mommy": "michelle",
    "rosa": "rosa",
    "yara": "yara",
    "gage": "gage",
    "gun_hut": "gage",
    "gunhut": "gage",
}
_EXPR_ALIASES = {
    "default": "smile",
    "look": "smile",
    "rest": "smile",
    "smirk": "tease",
    "tease": "tease",
    "blush": "smile",
    "heat": "tease",
    "sassy": "sassy",
    "greedy": "tease",
    "melt": "tease",
    "soft": "smile",
}
_FALLBACK = ["sassy", "tease", "default", "smile", "wink", "lean"]

# Old hardcoded map, used only if a file exists in _legacy or the character folder.
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


def _load_manifest() -> None:
    global _ALIASES, _EXPR_ALIASES, _FALLBACK
    if not MANIFEST_PATH.is_file():
        return
    try:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    if isinstance(data.get("aliases"), dict):
        _ALIASES = {str(k).lower(): str(v).lower() for k, v in data["aliases"].items()}
    if isinstance(data.get("expression_aliases"), dict):
        _EXPR_ALIASES = {str(k).lower(): str(v).lower() for k, v in data["expression_aliases"].items()}
    if isinstance(data.get("fallback_order"), list) and data["fallback_order"]:
        _FALLBACK = [str(x).lower() for x in data["fallback_order"]]


_load_manifest()


def load_shops(path: Path | None = None) -> dict:
    """Return the shops.json object as-is. Never drop entries."""
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


def npc_id(who: str) -> str:
    key = (who or "").strip().lower()
    return _ALIASES.get(key) or key.replace(" ", "_")


def portrait_path(filename: str) -> Path:
    """Resolve a bare filename against character folders, then _legacy, then flat."""
    name = Path(filename).name
    for folder in sorted(p for p in PORTRAITS_DIR.iterdir() if p.is_dir()) if PORTRAITS_DIR.is_dir() else []:
        hit = folder / name
        if hit.is_file():
            return hit
    return PORTRAITS_DIR / filename


def list_portraits() -> list[Path]:
    if not PORTRAITS_DIR.is_dir():
        return []
    out: list[Path] = []
    for p in PORTRAITS_DIR.rglob("*"):
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS:
            out.append(p)
    return sorted(out)


def _folder_for(who: str) -> Path | None:
    nid = npc_id(who)
    folder = PORTRAITS_DIR / nid
    if folder.is_dir():
        return folder
    if PORTRAITS_DIR.is_dir():
        for p in PORTRAITS_DIR.iterdir():
            if p.is_dir() and p.name.lower() == nid:
                return p
    return None


def portraits_for(who: str) -> dict[str, Path]:
    """NPC id or short name -> {expr: absolute Path} for files that exist."""
    nid = npc_id(who)
    out: dict[str, Path] = {}
    folder = _folder_for(nid)
    if folder:
        for p in folder.iterdir():
            if p.is_file() and p.suffix.lower() in IMAGE_EXTS:
                out[p.stem.lower()] = p
    # legacy flat files: mira-coffee.jpg sitting in portraits/ or _legacy/
    search_roots = [PORTRAITS_DIR, PORTRAITS_DIR / "_legacy"]
    for root in search_roots:
        if not root.is_dir():
            continue
        for p in root.iterdir():
            if not p.is_file() or p.suffix.lower() not in IMAGE_EXTS:
                continue
            stem = p.stem.lower()
            if stem.startswith(nid + "-"):
                expr = stem[len(nid) + 1 :]
                out.setdefault(expr, p)
            elif stem == nid:
                out.setdefault("default", p)
    # old hardcoded names, only if those files exist
    pack = PORTRAIT_EXPR.get(nid) or {}
    for expr, name in pack.items():
        p = portrait_path(name)
        if p.is_file():
            out.setdefault(expr, p)
    if "default" not in out:
        for key in _FALLBACK:
            if key in out:
                out["default"] = out[key]
                break
        if "default" not in out and out:
            out["default"] = next(iter(out.values()))
    return out


def _resolve_expr(pack: dict[str, Path], expr: str) -> Path | None:
    e = (expr or "default").lower()
    if e in pack:
        return pack[e]
    mapped = _EXPR_ALIASES.get(e)
    if mapped and mapped in pack:
        return pack[mapped]
    for key in _FALLBACK:
        if key in pack:
            return pack[key]
    if pack:
        return next(iter(pack.values()))
    return None


def portrait_texture_path(who: str, expr: str = "default") -> Path | None:
    pack = portraits_for(who)
    return _resolve_expr(pack, expr)


def portrait_asset_path(who: str, expr: str = "default") -> str | None:
    """Path relative to game ROOT, forward slashes — what Ursina load_texture needs."""
    p = portrait_texture_path(who, expr)
    if not p:
        return None
    try:
        return p.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return Path(p).as_posix()


def load_dialogue(who: str, path: Path | None = None) -> dict | None:
    nid = npc_id(who)
    p = path or (DATA / "dialogue" / f"{nid}.json")
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def list_character_ids() -> list[str]:
    if not PORTRAITS_DIR.is_dir():
        return []
    return sorted(
        p.name
        for p in PORTRAITS_DIR.iterdir()
        if p.is_dir() and not p.name.startswith("_")
    )


if __name__ == "__main__":
    print("characters:", ", ".join(list_character_ids()) or "(none)")
    for who in list_character_ids() or ["mira"]:
        pack = portraits_for(who)
        print(f"  {who}:")
        if not pack:
            print("    (no files)")
            continue
        for expr, p in sorted(pack.items()):
            print(f"    {expr:12} {p}")
        print("    resolve smile ->", portrait_texture_path(who, "smile"))
        print("    resolve heat  ->", portrait_texture_path(who, "heat"))


def load_npcs(path: Path | None = None) -> dict:
    p = path or (DATA / "npcs.json")
    if not p.is_file():
        return {}
    data = json.loads(p.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def load_mobs(path: Path | None = None) -> dict:
    p = path or (DATA / "mobs.json")
    if not p.is_file():
        return {}
    data = json.loads(p.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def load_items(path: Path | None = None) -> dict:
    p = path or (DATA / "items.json")
    if not p.is_file():
        return {}
    data = json.loads(p.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}

def _read_json(rel: str):
    p = DATA / rel
    if not p.is_file():
        p = ROOT / "data" / Path(rel).name
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def load_oss_items() -> dict:
    """CC-BY-SA CDDA workshop tools. Does not write shops.json."""
    data = _read_json("oss_items.json")
    items = data.get("items") or {}
    return items if isinstance(items, dict) else {}


def load_vehicles() -> dict:
    """Local park cars plus CDDA bike/moto catalog."""
    local = _read_json("vehicles.json")
    oss = _read_json("oss_vehicles.json")
    return {"local": local if isinstance(local, dict) else {}, "oss": (oss.get("vehicles") if isinstance(oss, dict) else None) or []}


def load_skills() -> dict:
    """Hollow skills plus CDDA skill ids for leveling."""
    hollow = _read_json("skills.json")
    oss = _read_json("oss_skills.json")
    return {"hollow": hollow if isinstance(hollow, dict) else {}, "oss": oss if isinstance(oss, dict) else {}}


def load_progression() -> dict:
    data = _read_json("progression.json")
    return data if isinstance(data, dict) else {}
