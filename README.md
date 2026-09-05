# Rune Mommy

Feminine neon **Clermont / Hwy 50** — a 3D desktop game (Ursina / Python). **Not a browser game.**

## Quick start (Windows 11, Python 3.10+)

```bat
py -3 -m pip install -r requirements.txt
py -3 game.py
```

If `py` is missing, use `python` instead of `py -3`.  
Need Python? https://www.python.org/downloads/windows/ — check **Add python.exe to PATH**.

A window titled **Rune Mommy** should open. Boot log prints `buildings=N quests=N tutorial=on/off`.

## Controls

| Key | Action |
|-----|--------|
| **WASD** | Walk |
| **Mouse** | Look |
| **Space** | Jump |
| **E** | Enter/exit car, talk, buy, POIs |
| **1** | Draw / holster pistol (Gage @ Hancock Gun Hut) |
| **LMB** | Shoot |
| **H** | Drink a shake (heals) |
| **Tab** | Free / lock cursor |
| **Enter** | Dismiss tutorial |
| **Esc** | Close talk panel, or quit |
| **1–4** | Dialogue choices |

You spawn on the **Sanctuary Drive** driveway. **Michelle** is at the front door (`door` dialogue node).

## World overview

- **E Hwy 50** — shake row, neon traffic, lot crowd, billboards
- **Sanctuary Drive** — Michelle’s teal-roof house + neighborhood labels
- **POIs** — gas / pumps, Palm Court Motel, laundromat, Green Siren kiosk, pharmacy, Willow pocket park
- **Quests** — starter log in `data/quests.json` (HUD `QUEST: …`, gold on complete)
- **Crowd / traffic** — `crowd.py` + `traffic.py` (caps kept for performance)

## Dev layout

| Path | Role |
|------|------|
| `game.py` | Main playable (~Game class). Prefer this for gameplay edits. |
| `game_launcher.py` / `_game_parts/` | Split-source rebuild for GitHub size limits |
| `models3d.py` | Composed Ursina meshes (houses, stalls, humanoids, cars) |
| `crowd.py` / `traffic.py` | Lot peds + Hwy 50 traffic |
| `loaders.py` | shops / NPCs / portraits / items |
| `vendor/` | Lightweight helpers (astar, steering, …) |
| `data/` | `shops.json`, `npcs.json`, `quests.json`, `dialogue/`, items, mobs |
| `client/portraits/` | Local-only face textures (may be missing on GitHub) |
| `docs/PLAYING.md` | Player guide |
| `docs/BUILDING.md` | How to add shop / NPC / quest |

## Content rules

- **Do not empty** `data/shops.json` — keep all **ten** Clermont shake stalls (+ gun hut).
- **Michelle** only — never invent / write **Lewis**.
- Michelle dialogue **start** stays `door`.
- Keep `open_vn` for **lila / rosa / yara** and `open_michelle`.
- Portraits may be **local-only** (binaries too large for some push paths).
- Desktop only — do not turn this into a browser client.
- Do not `git push` from automation unless a human asks.

## Tutorial

First boot (no `data/local_flags.json` / `tutorial_done`) shows a non-blocking overlay: WASD → E talk → mouse look → pistol → H shakes. **Enter** or finishing early steps writes `{ "tutorial_done": true }`.

## Graphics quality

Neon-dusk lighting + distance cull for crowds/traffic (`lighting.py`). See `docs/lighting.md`.

```bat
set RUNE_MOMMY_QUALITY=low
py -3 game.py
```

`low` / `med` (default) / `high`. Shadows only on `high`.
