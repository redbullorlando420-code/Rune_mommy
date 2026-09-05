# Playing Rune Mommy

3D Ursina desktop. Not a browser game.

## Install and run (Windows 11)

```bat
py -3 -m pip install -r requirements.txt
py -3 game.py
```

Graphics quality (optional):

```bat
set RUNE_MOMMY_QUALITY=low
py -3 game.py
```

`low` / `med` (default) / `high` — see `docs/lighting.md`.

## Mini tutorial (first minutes)

1. You spawn on **Sanctuary Drive** facing the house.
2. **WASD** walk, mouse look, **Space** jump.
3. Walk to the teal-roof door. **E** — Michelle walks the door beat (start node `door`). Quest *Door Duty* completes.
4. Read the HUD **QUEST** line. Next hooks: Mira Cool Down, Gage pistol, Club 27, Quiet Spa, Citrus Tower, Waterfront.
5. **E** on parked cars to drive; **E** again to bail.
6. Buy a pistol at Hancock Gun Hut (east). **1** draw, **LMB** shoot. Heat rises if you go loud.
7. **H** drinks a shake from your pack. Ten Clermont shake stalls stay on Hwy 50 — do not wipe them.

## Map pins

| Pin | Where | Who |
|-----|-------|-----|
| Sanctuary Drive | Spawn | Michelle (first name only) |
| The Shake Bar + nine shake stalls | Hwy 50 | Mira and stall NPCs |
| Hancock Gun Hut | East / Hancock | Gage |
| Club 27 Cabaret | 215 US-27 | Nova (hostess) |
| Quiet Spa | Hwy 50 west | Sori |
| Citrus Tower | North skyline | Tessa |
| Waterfront Park | South of Hwy 50 | Jules |
| Green Siren / Palm Court / Rx | Lot strip | barista / motel / pharmacist |

## Controls

- **WASD** walk · **Mouse** look · **Space** jump
- **E** talk / buy / enter-exit car
- **1** pistol · **LMB** shoot · **H** drink shake
- **Tab** free cursor · **Esc** close panel / quit · **1–4** dialogue picks

## Portraits

Put faces in `client/portraits/<npc>/` next to `game.py`. Light `.jpg`s may be on GitHub; full `.png`s are often local-only. See `docs/PORTRAITS.md` and run `py -3 loaders.py` to list what resolves.
