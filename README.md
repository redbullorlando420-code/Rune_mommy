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

Faces are **local files**, not always on GitHub.

1. Put images here, next to `game.py`:

```
client/portraits/<npc>/<expression>.png
```

Examples that already work on a full disk install:

```
client/portraits/mira/smile.png
client/portraits/michelle/sassy.png
client/portraits/lila/default.jpg
client/portraits/rosa/smile.png
client/portraits/yara/tease.png
```

2. The filename stem is the expression (`smile`, `sassy`, `tease`, …).
3. `loaders.portrait_asset_path()` turns that into a **relative** path like `client/portraits/mira/smile.png`. Ursina needs relative paths — absolute Windows paths return `None` and you get "mira portrait: missing".
4. Optional: `client/portraits/portraits.json` for aliases / fallbacks.
5. If you downloaded a zip from GitHub and portraits are missing, copy the `client/portraits/` folder from your other clone (for example `Documents\\Rune_mommy\\client\\portraits`) into this folder.

Smaller `.jpg` stand-ins may ship in the repo when the push path allows; full `.png`s often stay on disk only.

## What is in it

- Hwy 50 traffic, lot crowds, heat, fuel + vehicle damage
- Ten Clermont shake shops + Hancock Gun Hut (`data/shops.json` — do not empty)
- Club 27 Cabaret, Quiet Spa, Citrus Tower, Waterfront Park
- Mama Mira, Gage, Lila, Rosa, Yara, Michelle (first name only)
- Quests + mini tutorial (`data/quests.json`, on-screen tips)

## Docs

- `docs/PLAYING.md` — how to play
- `docs/BUILDING.md` — buildings / meshes
- `docs/TUTORIAL.md` — onboarding steps (if present)

## Data

Do not empty `data/shops.json`. Keep all ten shake stalls.
