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
