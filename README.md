# Rune Mommy

Pixel multiplayer browser game. Clermont shake row, Emberfen, Agate Mine.
Click the ground to walk. JS client uses WebSocket /ws.

## Python server (Windows 11, Python 3.11+)

```
py -3 -m pip install -r py/requirements.txt
py -3 py/server.py
```

Then open http://localhost:8080

`PORT` env var overrides the default 8080.

## Node server

npm start still runs the old Node server (`server/index.js`).

data/shops.json has the ten Clermont shake shops. Do not empty it.
