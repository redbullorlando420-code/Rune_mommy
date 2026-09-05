# Rune Mommy

3D desktop game (Ursina / Python). Clermont / Hwy 50. **Not a browser game.**

## Windows 11 (Python 3.10+)

Unzip or clone into a folder, open a terminal **in that folder**, then:

```bat
py -3 -m pip install -r requirements.txt
py -3 game.py
```

If `py` is missing, use `python` instead of `py -3`.

A window titled **Rune Mommy** opens. **Click the game window once**, then use WASD. Esc closes talk panels.

## Controls

- **WASD** walk (click the window first so it captures the mouse)
- **Mouse** look
- **Space** jump
- **E** enter/exit car, talk, buy, refuel at a pump
- **1** draw / holster pistol (buy from Gage at Hancock Gun Hut)
- **LMB** shoot
- **H** drink a shake (heals)
- **Tab** free the cursor
- **Esc** close talk panel, or quit
- **1–4** pick dialogue choices

You spawn in the **Sanctuary Drive** driveway. Walk to Michelle and press **E** (talk does not auto-open anymore).

## Portraits (important)

Faces live under **`client/portraits/` next to `game.py`**. Full steps: `docs/PORTRAITS.md`.

### Where on Windows

After unzipping a GitHub download, portraits go here (same folder that has `game.py`):

```
...\Rune_mommy-main\Rune_mommy-main\client\portraits\<npc>\<expression>.jpg
```

Example: `client\portraits\michelle\sassy.jpg`

### How the loader works

1. Put files in `client/portraits/<npc_id>/` — stem is the expression (`smile`, `sassy`, `tease`, …). Ext: `.jpg` / `.png` / `.webp`.
2. `loaders.py` maps names (`Mama Mira` → `mira`) and picks a file for that expression (with fallbacks).
3. `portrait_asset_path()` returns a **relative** path like `client/portraits/mira/smile.jpg`. Ursina needs that — absolute `C:\...` paths fail and you see `mira portrait: missing`.
4. Optional aliases: `client/portraits/portraits.json`.
5. Sanity check from the game folder: `py -3 loaders.py`

### What ships on GitHub

- **Light `.jpg` stand-ins** (under ~30KB) may be in the repo under `client/portraits/<npc>/`.
- **Full `.png` art** (~2MB each) usually stays **local-only** — copy `client/portraits/` from a full install into your Downloads unzip if faces are missing.

Do not empty `data/shops.json`. Michelle first name only.

## What is in it

- Hwy 50 traffic, lot crowds, heat, fuel + vehicle damage
- Ten Clermont shake shops + Hancock Gun Hut (`data/shops.json` — do not empty)
- Club 27 Cabaret, Quiet Spa, Citrus Tower, Waterfront Park
- Mama Mira, Gage, Lila, Rosa, Yara, Michelle (first name only)
- Quests + mini tutorial (`data/quests.json`, on-screen tips)

## Docs

- `docs/PORTRAITS.md` — face folders + how `loaders.py` works
- `docs/PLAYING.md` — how to play
- `docs/BUILDING.md` — buildings / meshes
- `docs/TUTORIAL.md` — onboarding steps (if present)

## Data

Do not empty `data/shops.json`. Keep all ten shake stalls.
