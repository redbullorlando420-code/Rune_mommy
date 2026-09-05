# Textures

Sources and licenses for files in this folder:

| File | Source | License |
|------|--------|---------|
| grass.jpg | AmbientCG Grass001 (Color map, resized 768) | CC0 1.0 |
| asphalt.jpg | AmbientCG Asphalt026B (Color map, resized 768) | CC0 1.0 |
| concrete.jpg | AmbientCG Concrete034 (Color map, resized 768) | CC0 1.0 |
| brick.jpg | AmbientCG Bricks075A (Color map, resized 768) | CC0 1.0 |
| stucco.jpg | Procedural original for Rune Mommy | original |
| water.jpg | Procedural original for Rune Mommy | original |

AmbientCG: https://ambientcg.com/ — CC0. Resized/compressed for repo size.

## Zip / GitHub note

Binary AmbientCG jpgs may stay **local-only** (MCP push truncates them). On first `py -3 game.py`, `assets/generate_textures.py` writes procedural PNG fallbacks (`grass.png`, `asphalt.png`, …) into this folder when jpgs are missing, so a fresh zip is not blank white. Prefer real jpgs from disk when present; `load_tex` checks `.jpg` before `.png`.
