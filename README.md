# Rune Mommy

3D desktop game set on Hwy 50 in Clermont, Florida. Native Python (Ursina). Not a browser client.

## Install (Windows 11)

```
py -3 -m pip install -r requirements.txt
py -3 game.py
```

`requirements.txt` is just `ursina`.

## How to play

- **WASD** walk
- **Mouse** look (Tab unlocks the cursor)
- **Space** jump
- **E** enter/exit a car, talk, or buy
- **1** draw / holster the pistol
- **LMB** shoot (need a gun from Gage)
- **Esc** close a talk panel, or quit

Cars sit in the Hwy 50 median. **Mama Mira** is at The Shake Bar (neon stall). **Gage** runs Hancock Gun Hut on the east edge of the pumps (pistol + ammo). Gold starts at 200.

## Shops

`data/shops.json` is the ten Clermont shake shops plus Hancock Gun Hut. Do not empty it.

The Shake Bar, Steak n Shake, Ritter's, Bruster's, Baskin-Robbins, Culver's, Five Guys, Dairy Queen, McDonald's, Wendy's.

## Layout

- `game.py` — desktop game
- `loaders.py` — shops + portraits
- `data/` — shops, items, NPCs, dialogue
- `py/` — Python ports of the old JS sim
