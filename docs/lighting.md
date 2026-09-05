# Lighting and performance

Rune Mommy uses a small **neon-dusk** light kit in `lighting.py` (Panda3D / Ursina patterns — not Project Zomboid source).

## Defaults

- One warm `DirectionalLight` (shadows **off** unless `RUNE_MOMMY_QUALITY=high`)
- Soft purple `AmbientLight` so silhouettes stay readable
- 1–2 `PointLight` accents (Hwy 50 neon + Sanctuary porch) — never a light per NPC
- Optional scene fog on med/high
- Crowd and traffic **distance cull**: far entities skip AI and hide meshes

## Quality env

```bat
set RUNE_MOMMY_QUALITY=low
py -3 game.py
```

| Value | Look | Cost |
|-------|------|------|
| `low` | Flat dusk, 1 point light, tighter cull | Fastest |
| `med` (default) | Neon accents + fog, no shadows | Balanced |
| `high` | Shadows on + third accent | Pretty, heavier |

## Files

- `lighting.py` — `apply_lighting`, `apply_perf`, cull helpers
- `crowd.py` / `traffic.py` — call cull helpers each tick
