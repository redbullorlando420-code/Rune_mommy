# vendor/

Small original implementations of classic public algorithms. Not a dumped GTA/MMO.

- `astar.py` — grid A* (8-connected, no corner cut). Public pathfinding algorithm.
- `noise2d.py` — seeded lattice value noise + fBm. Classic procedural noise.
- `fsm.py` — tiny named-state machine (`add` / `set` / `update`).
- `loot.py` — weighted choice + gold drop bands (civilian / thug / walker / barrel).
- `vehicle.py` — kinematic bicycle model (public vehicle kinematics).
- `spatial.py` — uniform cell spatial hash for nearby queries.
- `steering.py` — Reynolds seek / flee / wander heading (public steering behaviors).

Importable and unit-testable without Ursina. `python3 vendor/_smoke.py` prints `OK`.
