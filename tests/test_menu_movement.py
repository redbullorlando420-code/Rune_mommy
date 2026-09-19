"""Regression coverage for safe-yard startup input.

The game is intentionally split into source parts. This test extracts the
Game class without booting Panda3D, then exercises the exact menu -> safe-yard
-> WASD path that previously left the player suspended and unable to move.
"""
from __future__ import annotations

import ast
import importlib.util
import sys
import types
import unittest
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class Vec3:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x, self.y, self.z = float(x), float(y), float(z)

    def __add__(self, other):
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __iadd__(self, other):
        self.x += other.x
        self.y += other.y
        self.z += other.z
        return self

    def __mul__(self, value):
        return Vec3(self.x * value, self.y * value, self.z * value)

    __rmul__ = __mul__

    def length(self):
        return (self.x * self.x + self.y * self.y + self.z * self.z) ** 0.5

    def normalized(self):
        length = self.length()
        return self if not length else Vec3(self.x / length, self.y / length, self.z / length)


class Player:
    def __init__(self, x, y, z):
        self._position = Vec3(x, y, z)
        self.rotation_y = 0
        self.forward = Vec3(0, 0, 1)
        self.right = Vec3(1, 0, 0)

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        if isinstance(value, tuple):
            self._position = Vec3(*value)
        else:
            self._position = value

    @property
    def x(self):
        return self.position.x

    @x.setter
    def x(self, value):
        self.position.x = value

    @property
    def y(self):
        return self.position.y

    @y.setter
    def y(self, value):
        self.position.y = value

    @property
    def z(self):
        return self.position.z

    @z.setter
    def z(self, value):
        self.position.z = value


class MenuMovementTest(unittest.TestCase):
    def test_entrypoint_exposes_ursina_callbacks_from_main_module(self):
        """The stitched entry point must not hide `update`/`input` in a dict.

        Ursina discovers those callbacks on the actual main module. A private
        exec namespace renders the menu but drops keyboard input and movement.
        """
        entrypoint = (ROOT / 'game.py').read_text(encoding='utf-8')
        self.assertIn('_runtime_globals = globals()', entrypoint)
        self.assertIn('exec(compile(_src, str(_ROOT / "game.py"), "exec"), _runtime_globals, _runtime_globals)', entrypoint)
        self.assertNotIn('_ns = {"__name__": "__main__"', entrypoint)

    @classmethod
    def setUpClass(cls):
        source = ''.join(
            p.read_text(encoding='utf-8')
            for p in sorted((ROOT / '_game_parts').glob('part*.py.txt'))
        )
        tree = ast.parse(source, filename=str(ROOT / 'game.py'))
        game_node = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'Game')

        cls.mouse = types.SimpleNamespace(locked=False, visible=True, velocity=(0, 0))
        held_keys = defaultdict(int)
        fake_ursina = types.ModuleType('ursina')
        fake_ursina.application = types.SimpleNamespace(quit=lambda: None)
        fake_ursina.mouse = cls.mouse
        fake_ursina.held_keys = held_keys
        fake_ursina.raycast = lambda *args, **kwargs: None
        fake_ursina.Vec3 = Vec3
        fake_ursina.invoke = lambda callback, delay=0: None
        cls.original_ursina = sys.modules.get('ursina')
        sys.modules['ursina'] = fake_ursina
        namespace = {'__name__': 'menu_movement_test', '__file__': str(ROOT / 'game.py')}
        exec(compile(ast.Module(body=[game_node], type_ignores=[]), str(ROOT / 'game.py'), 'exec'), namespace)
        cls.Game = namespace['Game']

    @classmethod
    def tearDownClass(cls):
        if cls.original_ursina is None:
            sys.modules.pop('ursina', None)
        else:
            sys.modules['ursina'] = cls.original_ursina

    def make_game(self):
        game = self.Game.__new__(self.Game)
        game.mode = 'menu'
        game.ui_open = False
        game.mouse_free = False
        game.mouse = self.mouse
        game.move_keys = set()
        game.safe_yard_center = (80.0, 0.0, 80.0)
        game.player = Player(2, 6, 2)
        game.y_vel = 0.0
        game.grounded = False
        game.cam_pivot = types.SimpleNamespace(rotation_x=0.0)
        game.visual = types.SimpleNamespace(enabled=True)
        game.cam_in_car = False
        game.hud_toast = None
        game._set_menu_visible = lambda visible: None
        game._hide_play_hud = lambda hide: None
        game._lock_mouse = lambda locked: setattr(self.mouse, 'locked', bool(locked))
        game.toast = lambda message: None
        return game

    def test_menu_start_is_grounded_and_wasd_moves_with_mouse_look(self):
        game = self.make_game()
        game._enter_safe_zone()

        self.assertEqual(game.mode, 'safe')
        self.assertFalse(game.mouse_free)
        self.assertTrue(self.mouse.locked)
        self.assertEqual((game.player.x, game.player.y, game.player.z), (80.0, 0.0, 80.0))

        game.on_input('w')
        game._walk(0.1)
        self.assertGreater(game.player.z, 80.0)

        game.on_input('w up')
        self.assertFalse(game._movement_down(defaultdict(int), 'w'))

    def test_escape_from_safe_yard_returns_to_title(self):
        game = self.make_game()
        game._enter_safe_zone()
        game._show_menu = lambda: setattr(game, 'mode', 'menu')
        game.on_input('escape')
        self.assertEqual(game.mode, 'menu')

    def test_settings_round_trip_keeps_startup_input_unlocked(self):
        game = self.make_game()
        game._refresh_menu_labels = lambda: None
        game._enter_settings()
        self.assertEqual(game.mode, 'settings')
        self.assertTrue(game.mouse_free)
        self.assertFalse(self.mouse.locked)

        game._show_menu()
        game._enter_safe_zone()
        self.assertTrue(self.mouse.locked)
        game.on_input('d')
        game._walk(0.1)
        self.assertGreater(game.player.x, 80.0)

    def test_runtime_props_do_not_depend_on_missing_named_cylinder_model(self):
        florida_source = (ROOT / 'models3d' / '_florida.py').read_text(encoding='utf-8')
        self.assertNotIn("model='cylinder'", florida_source)
        self.assertIn('round_cylinder', florida_source)

    def test_camera_and_frame_loop_regressions_are_guarded_in_source(self):
        walk_source = (ROOT / '_game_parts' / 'part07.py.txt').read_text(encoding='utf-8')
        camera_source = (ROOT / '_game_parts' / 'part08.py.txt').read_text(encoding='utf-8')
        self.assertIn('self.cam_pivot.rotation_x += mouse.velocity[1] * sens', walk_source)
        self.assertIn('self._update_camera_collision()', walk_source)
        self.assertIn('def _update_camera_collision(self):', camera_source)
        self.assertIn('raycast(origin, delta.normalized()', camera_source)
        self.assertNotIn('_debug_tick(dt)', walk_source)

    def test_vehicle_driver_uses_bundled_bicycle_signature(self):
        spec = importlib.util.spec_from_file_location('test_vehicle', ROOT / 'vendor' / 'vehicle.py')
        vehicle = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(vehicle)
        result = vehicle.bicycle_step(0, 0, 0, 0, 0.4, 8, 0.1, vmax=24, wheelbase=2.6, drag=0.55)
        self.assertEqual(len(result), 4)
        driver_source = (ROOT / '_game_parts' / 'part07.py.txt').read_text(encoding='utf-8')
        self.assertNotIn('steer_gain=', driver_source)
        self.assertNotIn('coast_drag=', driver_source)
        self.assertNotIn('accel_drag=', driver_source)

    def test_layout_planner_rejects_house_road_overlap_without_override(self):
        spec = importlib.util.spec_from_file_location('test_layout', ROOT / 'world_layout.py')
        layout_module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = layout_module
        spec.loader.exec_module(layout_module)
        planner = layout_module.LayoutPlanner()
        self.assertTrue(planner.reserve('road', 'road', 0, 0, 20, 8, override=True))
        self.assertFalse(planner.reserve('house', 'residential', 0, 0, 4, 4))
        self.assertTrue(planner.reserve('house_ok', 'residential', 20, 0, 4, 4))

    def test_world_quality_features_have_source_regressions(self):
        roads = (ROOT / '_game_parts' / 'part04.py.txt').read_text(encoding='utf-8')
        crowd = (ROOT / 'crowd.py').read_text(encoding='utf-8')
        traffic = (ROOT / 'traffic.py').read_text(encoding='utf-8')
        lighting = (ROOT / 'lighting.py').read_text(encoding='utf-8')
        self.assertIn("self.layout.reserve('hwy_50', 'road'", roads)
        self.assertIn('def _build_enterable_interiors(self):', roads)
        self.assertIn('NEED_NODES =', crowd)
        self.assertIn('npc.need_target', crowd)
        self.assertIn('def _turn_toward(car, target_yaw, dt):', traffic)
        self.assertIn('tick_day_night', lighting)

    def test_menu_and_hud_text_use_the_ui_layer(self):
        menu = (ROOT / '_game_parts' / 'part02.py.txt').read_text(encoding='utf-8')
        hud = (ROOT / '_game_parts' / 'part06.py.txt').read_text(encoding='utf-8')
        self.assertIn('self.menu_title = Text(\n            parent=camera.ui,', menu)
        self.assertIn('self.hud_frame = Entity(parent=camera.ui', hud)
        self.assertIn("Text(parent=camera.ui, text='RUNE MOMMY'", hud)

    def test_regressions_for_dialogue_layout_and_vehicle_controls(self):
        hud = (ROOT / '_game_parts' / 'part06.py.txt').read_text(encoding='utf-8')
        driver = (ROOT / '_game_parts' / 'part07.py.txt').read_text(encoding='utf-8')
        camera = (ROOT / '_game_parts' / 'part08.py.txt').read_text(encoding='utf-8')
        safe_yard = (ROOT / '_game_parts' / 'part02.py.txt').read_text(encoding='utf-8')
        self.assertIn("position=(-0.47, -0.06)", hud)
        self.assertIn("steer_input = float(held_keys['d'] - held_keys['a'])", driver)
        self.assertIn("Vec3(0, 3.5, -11.0)", camera)
        self.assertIn("'kind': 'pistol'", safe_yard)

    def test_geometry_and_highway_expansion_are_stable(self):
        roof = (ROOT / 'models3d' / '_base.py').read_text(encoding='utf-8')
        world = (ROOT / '_game_parts' / 'part04.py.txt').read_text(encoding='utf-8')
        traffic = (ROOT / 'traffic.py').read_text(encoding='utf-8')
        self.assertNotIn('rotation_z=pitch', roof)
        self.assertIn('scale=(760, 1, 660)', world)
        self.assertIn("'hwy_loop': ((-295, -16)", traffic)

    def test_life_sim_and_vehicle_service_regressions(self):
        crowd = (ROOT / 'crowd.py').read_text(encoding='utf-8')
        car = (ROOT / 'models3d' / '_actors.py').read_text(encoding='utf-8')
        driving = (ROOT / '_game_parts' / 'part07.py.txt').read_text(encoding='utf-8')
        gas = (ROOT / '_game_parts' / 'part10.py.txt').read_text(encoding='utf-8')
        self.assertIn('SOCIAL_LINES =', crowd)
        self.assertIn('ped.bubble = game.Text', crowd)
        self.assertIn('car.max_damage = 240.0', car)
        self.assertIn("getattr(car, 'max_damage', 240.0)", driving)
        self.assertIn('def _gas_air(self, car):', gas)


if __name__ == '__main__':
    unittest.main()
