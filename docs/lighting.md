# Lighting and performance

Rune Mommy uses a small **neon-dusk** light kit in `lighting.py` (Panda3D / Ursina patterns — not Project Zomboid source).

## Defaults

- One warm horizon `DirectionalLight` (2048px shadows only at `RUNE_MOMMY_QUALITY=high`)
- Cool blue-hour `AmbientLight` so silhouettes and Florida foliage stay readable
- 1–3 `PointLight` accents on medium, 5 on high (Hwy 50, Sanctuary, waterfront, Club 27) — never a light per NPC
- Blue-hour distance fog on med/high and 4× MSAA at high
- Pooled, camera-relative firefly/dust particles (18 on medium, 30 on high); no per-frame allocation
- Crowd and traffic **distance cull**: far entities skip AI and hide meshes
- A visual-only 7.5-minute day/night cycle updates the existing sun, ambient
  fill, and sky; it creates no lights or materials during the frame loop

## Quality env

```bat
set RUNE_MOMMY_QUALITY=low
py -3 game.py
```

| Value | Look | Cost |
|-------|------|------|
| `low` | Flat dusk, 1 point light, no ambient particles, tighter cull | Fastest |
| `med` | Blue-hour fog, 3 accents, 18 ambient particles, no shadows | Balanced |
| `high` (default) | 4× MSAA, 2048px shadows, 5 accents, 30 ambient particles | Pretty, heavier |

## Files

- `lighting.py` — `apply_lighting`, `apply_perf`, cull helpers
- `crowd.py` / `traffic.py` — call cull helpers each tick
- `world_layout.py` — deterministic road/commercial/residential footprints
