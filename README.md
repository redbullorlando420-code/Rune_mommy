# Rune Mommy

3D desktop game (Ursina / Python). Clermont / Hwy 50. **Not a browser game.**

## Windows 11 (Python 3.10+)

Open a terminal in this folder, then:

```bat
py -3 -m pip install -r requirements.txt
py -3 game.py
```

A window titled **Rune Mommy** should open. If `py` is missing, use `python` instead of `py -3`.

Need a Python install? https://www.python.org/downloads/windows/ — check **Add python.exe to PATH**.

## Controls

- **WASD** walk
- **Mouse** look
- **Space** jump
- **E** enter/exit a parked car, talk, buy
- **1** draw / holster pistol (buy one from Gage at Hancock Gun Hut)
- **LMB** shoot
- **H** drink a shake (heals)
- **Tab** free the cursor
- **Esc** close talk panel, or quit
- **1–4** pick dialogue choices

You spawn in the **Sanctuary Drive** driveway. Michelle is at the front door.

## What is in it

- Overflowing Hwy 50 traffic and a lot crowd (shoot, loot gold, heat)
- Ten Clermont shake shops plus Hancock Gun Hut (`data/shops.json` — do not empty it)
- Mama Mira, Gage, Lila, Rosa, Yara, and **Michelle** (Sanctuary Drive). Michelle only — no last name.

## Portraits

Faces live on disk under `client/portraits/<name>/` (for example `michelle/sassy.png`). They are **local-only** — not shipped on GitHub (the connector cannot push image binaries cleanly). Keep that folder next to `game.py` when you play. Small jpg stand-ins also live in those folders on the box/RB24.

## Data

Do not empty `data/shops.json`. Keep all ten shake stalls.
