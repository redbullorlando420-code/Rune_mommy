# Rune Mommy

3D desktop game (Ursina). Pixel-hot Clermont / Emberfen. Not a browser app.

`data/shops.json` holds the ten Clermont shake shops (do not empty it).

## Windows 11

1. Install Python 3.11+ from https://www.python.org/downloads/ (check **Add python.exe to PATH**).
2. Open a **new** PowerShell in this folder.

```powershell
py -3 -m pip install ursina
py -3 game.py
```

Or:

```powershell
py -3 -m pip install -r requirements.txt
py -3 game.py
```

If `py` is not recognized, reopen Terminal after installing Python, or use `python` instead of `py -3`.

## Loaders

`loaders.py` reads `data/shops.json` and `client/portraits/` for the desktop game. Do not strip shops.
