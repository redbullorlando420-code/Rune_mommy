# Open-source and asset attribution

## Runtime model layer

Rune Mommy's runtime uses [Ursina](https://github.com/pokepetter/ursina), an
MIT-licensed open-source Python 3D engine built on Panda3D. The project uses
Ursina's Entity/billboarding rendering path and a project-local procedural mesh
layer; no external binary model pack is bundled in this repository.

## Project-authored additions

`models3d/_base.py` provides project-authored, cached round-cylinder and
high-detail head meshes. `models3d/_florida.py` composes them into palms,
live-oak canopies, utility poles, shoreline water, and a pooled ambient particle
layer. The code can be audited, modified, and distributed with the rest of the
repository.

## Project-local generated materials

- `assets/characters/hero_face_v1.png` — 1024px neutral dialogue-portrait material.
- `assets/textures/hero_fabric_v1.png` — 1024px seamless teal knit outfit material.
- `assets/textures/sky_dusk_v1.png` — high-resolution blue-hour sky backdrop.
- `textures/cog.png` and `textures/rune_mommy.ico` — project-generated runtime
  compatibility assets for incomplete Ursina installations.
- `assets/fonts/OpenSans-Regular.ttf` — a project-local Open Sans UI font
  (Apache License 2.0) so menus do not depend on Ursina package layout.

The first two are generated for this project with OpenAI image generation and
are game-local assets, not downloaded third-party models or branded material.

Before adding any downloaded `.glb`, `.gltf`, texture pack, sound, or character
model, record its source URL, creator, license, modification, and attribution
text here. Do not ship assets without a license compatible with this project.
