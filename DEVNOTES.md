# DEVNOTES — life-sim, interiors, Florida slice

## Enterable interiors
Walk up to an **orange door mat** and press **E**:
- **Michelle house** (Sanctuary Drive front)
- **Quiet Spa**
- **Club 27**
- **Gas shop** counter
- **Walmart** (far east Hwy 50) — blue register / **E** opens shop shelves (`walmart_clermont` in `data/shops.json`)

Inside: green mat = **E** to exit. Outdoor building colliders stay; rooms live in a far pocket so the lot is untouched.

## Life-sim (schedule-based)
`life_sim.py` advances an accelerated in-game clock and drives a light FSM:

| State | Meaning |
|-------|---------|
| home | at residence / porch |
| work | on shift (Mira, Gage, spa, Club 27, Rita) |
| shop | errands |
| wander | sidewalk roam |
| talkable | E still works; line mentions current state |

Michelle + named NPCs + every 4th crowd ped participate. Visibility uses `set_visible` / `y>=0` so they stay readable after leaving the safe yard. **Michelle is never given a last name / deadname** — first name only.

## Food trucks
Three trucks from `data/shops.json` (`kind: food_truck`) — Cuban, Gator bites, Midnight. **E** uses the existing shake-shop buy panel. Core ten shakes + gun hut were **not** wiped.

## Lakes + alligators
`wildlife.py`: deep lake (surface + basin, darker center) SE of town; smaller pond west. Player **y sinks** while wading. Gators idle → chase → bite (`_hurt`). Shoot to kill; loot Gator Meat / Gator Hide.

## Map densify
`models3d/_extras.densify_hwy50` adds houses / kiosks along Hwy 50. Pitched roofs use existing A-frame **±28** (ridge at wall-top+0.55). Ground Y uniqueness: lot **0.02**, sidewalk **0.07**, hwy **0.09**, paint **0.12**.

## Files
- `life_sim.py`, `interiors.py`, `wildlife.py`
- `models3d/_extras.py` (+ exports in `models3d/__init__.py`)
- `data/shops.json` append-only trucks/Walmart; `data/items.json` snack/loot ids
- `game.py` thin hooks (`_build_deferred_content`, tick/interact/prompt)

## Tokyo / Akihabara
- **Find portal**: Clermont torii/arch at approx **(16, 3.5)** — north of Hwy 50 near the plaza/gas strip. Pink mat + vermillion gate, sign **秋葉原 / AKIHABARA**. **E** or walk onto the mat.
- **Return**: In Akihabara, torii near the station plaza (**CLERMONT ←**). **E** / walk-in.
- **Pins**: Akihabara Station, Radio Kaikan, Super Potato, Animate, Don Quijote (Donki), Mandarake, Yodobashi, UDX, Electric Town spine.
- Modules: `tokyo.py`, `akihabara.py`, `models3d/_tokyo.py`. District origin **(480, 0, 0)**.

## Michelle dialogue
- Clickable choice **Buttons** + keys **1–8** (`dialogue_ui.py` contract; wired in HUD panel).
- Branching openings via `michelle_talk.pick_michelle_opening` (breed/preg/life-sim/heat/hour).
- Mesh: `style='michelle'` in `models3d/_actors.py` — teal dress hourglass silhouette.

## TODO (next slices)
- **Parking lots / NPC drivers**: done — **edge lots** (`parking.py` + `traffic.py`).
- **Car crash physics / destruction / chunk streaming**: later.
- **Map builder tool**: F-key/grid placer → `data/map_layout.json`.

## Radar / waypoints / missions (2026-09-19)
- `radar.py`: top-down minimap (player / quest / POIs) + compass arrow + world beacon.
- Quest board expanded in `data/quests.json` (~40+ NPC talk/visit/kill chains).
- HUD still shows active quest line; compass points at quest NPC/POI.

## Parking + NPC drivers
- `parking.py`: marked lots (plaza/gas/club27/spa/walmart), stall occupancy.
- `traffic.py`: highway cars spawn **with NPC drivers**; empty cars sit in lots.
- Cars without a live driver seek a stall and park; player `_enter_car` unseats driver.

## Graphics — RUNE_MOMMY_QUALITY
- `low` | `med` | `high` (default) | **`ultra`**
- high/ultra: shadows, more neon point lights, denser fog control.
- PRC: MSAA 4/8, anisotropic 8/16, NVIDIA-friendly texture filters (`lighting.apply_perf`).
- Example: `set RUNE_MOMMY_QUALITY=ultra` then `py -3 game.py`

## Sexier meshes
- `models3d/_actors.py`: Michelle hourglass/hair/chest/skirt pushed further; named NPCs get soft bust; hitbox ghost unchanged.

## Crowd / life-sim densify
- `crowd.PED_COUNT` 40; life_sim every 3rd ped + more POI anchors.

## Perf / FPS — RUNE_MOMMY_FPS (2026-09-19)
- `RUNE_MOMMY_FPS` target (default **60**, hard floor 60). PRC `clock-mode limited` + `clock-frame-rate` + vsync on med/high/ultra.
- Interacts with `RUNE_MOMMY_QUALITY`: ultra keeps MSAA8/aniso16/shadows; **LOD + AI throttle** protect the 60 budget.
  - Peds/cars: distance cull, `set_lod` near/mid (hide `lod_detail=high` extras), far agents tick every N frames (`ai_far_interval`).
  - Example: `set RUNE_MOMMY_QUALITY=ultra` and `set RUNE_MOMMY_FPS=60` then `py -3 game.py`

## Road avoid (crowd / life_sim)
- Hwy 50 asphalt corridor ≈ **z ∈ [-19.5, -12.5]**. Foot traffic spawns/steers onto sidewalks (**z≈-10.6 / -21.4**) and lots.
- `crowd.is_on_road` / `steer_off_road` / `clamp_destination`; life_sim destinations clamped.

## Retail append (shops.json — never wipe)
- `pet_store_clermont`, `bestbuy_clermont`, `gamestop_clermont`, `tire_shop_clermont`, `nail_salon_clermont`
- Japan/Tokyo akihabara shops kept. Enter via orange door mats / E shop.

## Tire wear
- Cars accumulate `tire_wear` 0–100 from speed, hard steer, off-hwy, hard brake.
- Scales `steer_gain` down and drag up via `_bicycle_step_safe` (vendor API unchanged).
- **Hwy 50 Tire & Lube** (`tire_shop_clermont`): patch 25g (−40), balance 35g (−22), new set 90g (reset). HUD: `TIRES N%`.

## Parking — edge lots
- Downtown plaza/gas pads **removed**. Lots live at map edge: `edge_nw`, `edge_sw`, `edge_ne`, `edge_se`, `edge_hwy_e` with painted exits toward Hwy 50 / arterials. Empty cars still seek stalls.

## Adult minigames (`adult_minigames.py`)
- **Neon Toes** pedicure lounge (adult foot session) — E at salon / dialogue hook.
- **Michelle intimacy** — dialogue `action: sex_minigame` or guest/shower room after meeting her. Mesh toggles clothed → underwear → nude (`michelle` / `_underwear` / `_nude`) (adult only). First name only.

## Meshes
- Adult feminine anime_f (Michelle, named women, female crowd): hourglass, longer hair, eye spheres, skirts/thighs.
- Male/thug/walker stay utilitarian. HD `make_car`: mirrors, trim, rims, LOD tags on extras.


## Camera modes (2026-09-19)
- Keys **V** / **C** or mouse **wheel**: cycle Follow → Near/Shoulder → Far/Chase (+ **Hood** in car).
- Preference lightly in flags (`cam_mode`) + local save. Toast shows mode name. Esc/Tab mouse lock unchanged.

## Outfit states (adult)
- Feminine adults + player: **U** cycles clothed → underwear → nude (`clear_humanoid_parts` + re-attach).
- Michelle: dress / underwear / nude (intimacy still uses nude). First name only.

## Crowd / traffic density
- `crowd.PED_COUNT` **40** (~50% cut). Traffic loops 3+3+3, empty parked **5** (~60% cars cut). Better meshes, fewer agents.


## Boot fixes (2026-09-19 CoS)
- **60 FPS**: Ursina `apply_settings` forces `vsync=True`→`MNormal` after ShowBase; we `pre_boot_fps_prc()` + `apply_fps_cap()` (MLimited + `window.vsync=int(fps)` + `sync-video false`). DBG uses `dt_unscaled`.
- **Density**: `PED_COUNT=40`; traffic 3+3+3 + 5 empty; lot cars 4; Aki crowd 8 (not in `peds`).
- **CJK**: Tokyo/Aki signs ASCII only (no font spam).
- **Icon**: `textures/ursina.ico` shipped; boot points Ursina icon there.
- **Dedupe**: buildings/quests print once; gators one line; SAFE YARD toast once.
- **Footprints**: `footprints.py` AABB — densify + retail nudge off roads/lakes/each other; boot log `footprints: placed=…`.
- **Chunks**: `chunks.py` stub — coarse 32 / micro 8, hide far peds/cars (LOD assist).

## Perf emergency (2026-09-19 evening)
- **Title menu slim boot**: setup builds ONLY safe yard + player + HUD + menu. Full Clermont (ground/hwy/skyline/town/POIs/house/stalls/NPCs/cars/targets/crowd/traffic/deferred densify+wildlife+interiors+life_sim+Tokyo portal) runs on pink-gate via `_ensure_world_populated()`.
- **Akihabara deferred**: `tokyo.boot` builds Clermont portal only; `ensure_akihabara()` builds district on first portal enter.
- **Quality default `med`**; shadows **ultra-only**; high point lights capped at 2; tighter cull/LOD; aggressive `set_lod` hides untagged humanoid children at mid.
- **Menu buttons**: empty `Button` + separate `Text` labels (fixes white pixel garbage from Button font atlas).
- **Textures**: `load_tex` searches `assets/textures` + `textures`, prints misses; boot logs loaded/missing.
- **Icon**: tiny valid BMP-ICO at `textures/ursina.ico` (skip if header invalid).
- **Dedupe**: SAFE YARD toast once (no double print); gators print once via `_gators_printed`.
- **ASCII**: `CLERMONT <-` (no U+2190).
- Adult mesh: visible nipples + light `tick_jiggle` stub; deeper waifu mesh next green after FPS stable.

## Mesh orientation + spawn plaza (2026-09-19)
- Humanoid local **+Z = face forward** (eyes/nose/lips). Bust/cleavage/nipples on **+Z**; butt cheeks / hip flare on **-Z**. Clothed / underwear / nude aligned.
- `tick_jiggle`: damped spring on tagged bust/hip; game ticks Michelle + nearby feminine only (LOD near ~22m); skip culled.
- `footprints.py`: spawn plaza **r=32** at `clermont_spawn` / gate exit + Sanctuary **r=14**. Town houses, POIs, stalls, retail, densify all `place_or_nudge`. Boot logs `OVERLAPS remaining=N`.
- Slim boot / deferred populate / Aki defer / PED_COUNT=40 / quality med unchanged. No git push.

## Walk-in stores + bust scale + talk freeze (2026-09-19)
- **No far-XYZ pocket teleport.** Stores are true walk-in: hollow shells with south (Sanctuary: east) door gaps; interiors.py fills shelves/counters/lights co-located with the building footprint. Orange mat is visual only. Walk in / walk out; **E** opens shop when inside.
- Covered: shakes (stall shells), Walmart, BestBuy, GameStop, pet, tire, nail, gas, spa, Club 27, Sanctuary.
- Materials: `_safe_tex` skips bare path strings so missing Ursina loads fall back to solid color (no pink/miss).
- **Bust scale** reduced toward natural adult proportions (Michelle dress/underwear/nude + anime_f). Nipples remain on nude; light jiggle; bust still **+Z** forward.
- **Talk freeze**: `talk_target` / `talk_frozen` — crowd + life_sim hold position and face player while dialogue panel is open; cleared on `close_panel`.
- Slim boot / deferred populate / PED 40 / footprints spawn plaza keep-out / shops.json append-only / no git push.

## Feel pass — crash / drive / audio (2026-09-28)
- **Crash physics** (`crash.py`): car-vs-car + car-vs-world impulse, damage cooldown, smoke @55+, disable @100, cheap cube debris (cap 18, cull ~42m). Player `_drive` uses `crash.resolve_player_hit`; traffic soft-separates + can take ram damage.
- **Tighter driving**: vendor `bicycle_step` handbrake yaw + snappier vmax/accel (26/20); Space handbrake oversteer; tire_wear still scales grip. `_bicycle_step_safe` unchanged (filters unknown kwargs).
- **Audio** (`sfx.py` + `assets/sfx/*.wav` procedural stubs): engine loop, impact, horn (**F** in car), UI beeps. `RUNE_MOMMY_AUDIO=0` keeps null backend. Missing device → silent stubs.
- Perf: slim title boot / deferred populate / PED 40 / quality **med** / talk-freeze / footprints / orientation keep. Shops untouched. No git push.
- Test: enter car on Hwy 50 → W accel, Space handbrake slide, ram traffic or wall (DMG/smoke/debris), F horn, gas repair. Watch FPS (med, debris capped).
