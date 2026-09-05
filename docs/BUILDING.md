# Building content (shops / NPCs / quests / meshes)

## Rules

- Never empty `data/shops.json` (ten shakes + gun hut).
- Never write Lewis. Michelle only. Door start stays `door`.
- Prefer `models3d.py` helpers over raw cubes.

## Clermont pins Coder is meshing

- Club 27 Cabaret — 215 US-27 (`club27_host` / Nova)
- Quiet Spa — Hwy 50 west (`quiet_spa_tech` / Sori)
- Citrus Tower — north (`citrus_guide` / Tessa, poi `citrus_tower`)
- Waterfront Park — south (`park_ranger` / Jules)

Place meshes in `Game._build_pois` / `models3d`; wire **E** range to the NPC stubs in `data/npcs.json`.

## Add a talkable NPC

1. Append `data/npcs.json`: `id`, `name`, `kind` (`talk` or VN id), `color`, `greet`, `lines`.
2. Place in `Game._build_npcs` `talk_spots` (and a POI if needed).
3. VN (lila / rosa / yara): `data/dialogue/<id>.json` + `open_vn`. Michelle: `open_michelle`, start `door`.

## Add a quest

Edit `data/quests.json`. Types: `talk`, `buy`, `buy_pistol`, `kill`, `michelle_room`, `visit` (poi id).

Use `requires` for unlock order; `auto_start` on the tutorial.

## Add a shake shop

Append only. Keep existing ten. Stock ids must exist in `data/items.json`.

## Docs set

- `docs/PLAYING.md` — run + tutorial
- `docs/BUILDING.md` — this file
- `docs/TUTORIAL.md` — step checklist for QA
- `docs/lighting.md` — quality / cull
