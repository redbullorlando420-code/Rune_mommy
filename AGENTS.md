# Rune Mommy game-agent verification procedure

Run this procedure after any change to menus, input, player movement, models,
textures, lighting, or packaged assets.

1. Run `python -B tests/test_menu_movement.py`. It must pass both menu-start
   and Settings → Back → Start movement paths.
2. Compile the stitched runtime without executing it:
   `python -B -c "from pathlib import Path; p=Path('_game_parts'); compile(''.join(x.read_text(encoding='utf-8') for x in sorted(p.glob('part*.py.txt'))), 'game.py', 'exec')"`
3. Run `python game.py`, choose **Start**, hold each of `W`, `A`, `S`, and `D`,
   and confirm the player starts grounded and moves in every direction.
4. Return to the menu with Esc; open **Settings**, go back, choose **Start**,
   and repeat the movement check. Mouse-look must be active after Start; Tab
   must release and recapture the cursor without interrupting movement.
5. Review startup output. Treat `missing model`, `missing texture`, `missing
   icon`, or missing portrait warnings as failures; use project-local assets or
   procedural meshes instead of unresolved model-name strings.
6. At `RUNE_MOMMY_QUALITY=high`, visually inspect the hero, Michelle, one
   named NPC, palms, lighting, fog, and particles. Verify the frame rate stays
   playable and no new fallback/error messages appear.
7. Leave the safe yard through the pink gate. Confirm mouse-look remains
   responsive, moving the mouse up looks up, Tab still releases/re-captures
   the cursor, and the follow camera pulls forward instead of showing through
   a floor, vehicle, or building wall. Startup output must contain no `DBGERR`.
8. At the gas pump on foot, press **E**. Confirm Hancock Gas Market loads,
   walking still works inside, and **E** returns outside. Drive one full Citrus
   Run loop and confirm traffic turns progressively rather than snapping.
9. Review startup output for `no valid commercial parcel`. It must be absent.
   Run `python -B tests/test_menu_movement.py`; its road/house planner test
   must reject an overlapping house unless the placement explicitly overrides it.
