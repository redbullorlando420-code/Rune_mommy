# Rune Mommy

A cozy click-to-walk **3D** multiplayer browser MMORPG. Pick a display name (no accounts), wander Clermont, sip shakes, forage the Emberfen wilds, fight critters, chat, and trade.

Flagship hangout: **The Shake Bar** (2545 E Hwy 50) — neon milkshake stall run by Mama Mira. Best-seller: **The Cool Down**.

Original game. Not affiliated with Jagex. Restaurant names and Clermont / Hwy 50 addresses are in-world flavor only.

## Run locally

Requires Node.js 18+.

```
npm install
npm start
```

Open http://localhost:8080 in two browser windows with two names. The same `npm start` process serves the Three.js client and the WebSocket game server.

## The shake row (starter town)

Ten Clermont shake shops as 3D buildings / buyable NPC stalls. Catalog lives in `data/shops.json` (do not delete the ten shops).

Spawn is the fountain plaza. The Shake Bar is the glowing magenta stall on Hwy 50. East of town is Emberfen Hollow (second town, shrine, keeper). Southeast is the Agate Mine. South is Johns Lake strip.

## Controls

- Walk: left-click the ground
- Orbit camera: right-drag, scroll to zoom
- Talk, shop, attack, gather: left-click the target
- Trade: click another player, then Trade
- Use / drink: click an item in the pack (I)
- Chat: type at the bottom, Enter. Whisper: `/w Name hello`

## Two-window smoke test

1. `npm start`
2. Window A name MiraFan. Window B name HwyWalker.
3. Walk. You should see the other body move in 3D.
4. Chat hey. Whisper with `/w HwyWalker secret`
5. Walk north to The Shake Bar, click Mama Mira, buy The Cool Down
6. Click the other player, Trade, put the Cool Down or gold in, both lock then Accept
