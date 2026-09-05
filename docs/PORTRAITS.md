# Portraits and the image loader

Faces are loaded by `loaders.py` (next to `game.py`). Ursina needs a **path relative to the game folder**, not a full Windows `C:\...` path.

## Where files live on this build

```
Rune_mommy/
  game.py
  loaders.py
  client/
    portraits/
      mira/
        default.jpg
        smile.jpg
        tease.jpg
        ...
      michelle/
        sassy.jpg   # light stand-in (on GitHub when shipped)
        sassy.png   # full art — often local-only (~2MB)
      lila/
      rosa/
      yara/
      portraits.json   # optional aliases
      _legacy/         # old flat names like mira-coffee.jpg
```

On Windows after a Downloads zip, that is usually:

`C:\Users\<you>\Downloads\Rune_mommy-main\Rune_mommy-main\client\portraits\`

## Put a new face here

1. Create a folder named after the NPC id: `client/portraits/<npc_id>/`
2. Drop `smile.jpg`, `default.png`, `tease.webp`, etc. Stem = expression. Ext can be `.jpg` / `.jpeg` / `.png` / `.webp`.
3. Restart the game (`py -3 game.py`).

Example:

```
client/portraits/mira/smile.jpg
client/portraits/michelle/sassy.png
```

## How the loader finds them

1. `npc_id("Mama Mira")` → `mira` (aliases in code / optional `portraits.json`).
2. Look in `client/portraits/mira/` for files.
3. Fall back to `_legacy/` and old flat names (`mira-coffee.jpg`).
4. Expression aliases (e.g. `heat` → `tease`, `default` → `smile`) then a fallback list.
5. `portrait_asset_path(who, expr)` returns something like `client/portraits/mira/smile.jpg` for Ursina `load_texture`.

Quick check from the game folder:

```bat
py -3 loaders.py
```

That prints each character and which files resolved.

## GitHub zip missing faces

Full `.png`s are often **too big for GitHub** (~2MB each) and stay on disk only. Lighter `.jpg` stand-ins may ship under `client/portraits/<npc>/`.

If the log says `mira portrait: missing`:

1. Confirm `client/portraits/` exists **next to** `game.py` in the folder you are running.
2. Copy that folder from a full install (another clone / USB / Discord drop).
3. Re-run `py -3 game.py` from that same folder (not from a parent directory).

## Do not

- Put portraits only on the Desktop and expect the Downloads zip to see them.
- Pass absolute Windows paths into Ursina by hand — `loaders.portrait_asset_path` already returns relative paths on purpose.
