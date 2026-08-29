# Rune Mommy

3D multiplayer browser MMO. Clermont shake row (10 shops), Emberfen wilds, Agate Mine, chat, 2-sided trade, gathering, combat.

Repo: https://github.com/redbullorlando420-code/Rune_mommy

## Run

Need Node.js 18+.

```
npm install
npm start
```

Open http://localhost:8080 in two browser windows. Names: 2-16 characters, start with a letter. You should see each other walk.

## Controls

- Left-click ground: walk (click-to-walk)
- Left-click shop / NPC / tree / beast: talk, shop, gather, or attack
- Left-click another player: Trade
- Right-drag: orbit camera. Wheel: zoom
- Chat + Enter. Whisper: `/w Name hi`. `/who` `/help`
- I pack, K arts, M places, B bind at the shrine, Esc closes windows

## World

72 x 56 tiles.

- North: Hwy 50 shake row (Baskin, Bruster's, The Shake Bar, Steak n Shake, Ritter's)
- Center: Clermont Square / First Fire (spawn)
- South: Johns Lake strip (DQ, Five Guys, Culver's, McD, Wendy's)
- East: Emberfen Hollow (Maera, Voss, Binding Shrine) and Agate Mine

`data/shops.json` is the 10 Clermont shake shops. Do not empty it.

Starter pack includes 80 ember coins (Cool Down at The Shake Bar is 42).
