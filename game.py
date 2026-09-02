"""Rune Mommy — 3D desktop (Ursina). No browser.
Controls: WASD walk, mouse look, Space jump, E enter/exit car or talk, LMB shoot, Esc quit.
"""
from pathlib import Path
import math

from ursina import (
    scene, Ursina, Entity, camera, color, held_keys, raycast, time,
    Text, Vec3, application, Sky, DirectionalLight, AmbientLight,
)
from ursina.prefabs.first_person_controller import FirstPersonController
from loaders import shop_list

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
PORTRAITS = ROOT / "client" / "portraits"

app = Ursina(title="Rune Mommy", borderless=False, fullscreen=False, development_mode=False)
from ursina import window as win
win.size = (1280, 720)
win.fps_counter.enabled = True

Sky(color=color.rgb(40, 30, 55))
DirectionalLight(y=3, z=3, rotation=(45, -20, 0))
AmbientLight(color=color.rgba(140, 120, 160, 180))

ground = Entity(
    model="plane",
    scale=(120, 1, 120),
    color=color.rgb(28, 70, 36),
    texture="white_cube",
    texture_scale=(60, 60),
    collider="box",
)
Entity(model="cube", scale=(80, 0.12, 8), position=(0, 0.06, -18), color=color.rgb(45, 42, 48), collider="box")

shops = shop_list()
stall_colors = [
    color.rgb(255, 79, 216), color.rgb(245, 213, 71), color.rgb(255, 143, 171),
    color.rgb(214, 40, 40), color.rgb(233, 30, 140), color.rgb(30, 75, 142),
    color.rgb(211, 47, 47), color.rgb(227, 24, 55), color.rgb(255, 199, 44),
    color.rgb(228, 28, 56),
]
for i, s in enumerate(shops):
    x = -28 + (i % 5) * 12
    z = -22 - (i // 5) * 10
    col = stall_colors[i % len(stall_colors)]
    Entity(model="cube", scale=(4, 3, 3), position=(x, 1.5, z), color=col, collider="box")
    label = Entity(parent=scene, position=(x, 3.4, z))
    Text(text=s.get("name", "Shop")[:16], parent=label, scale=8, billboard=True, color=color.white, origin=(0, 0))

Entity(model="cube", scale=(5, 3.2, 4), position=(22, 1.6, -6), color=color.rgb(80, 70, 50), collider="box")
gl = Entity(position=(22, 3.6, -6))
Text(text="Gun Hut", parent=gl, scale=10, billboard=True, color=color.orange, origin=(0, 0))

mira_tex = str(PORTRAITS / "mira-coffee.jpg") if (PORTRAITS / "mira-coffee.jpg").exists() else None
mira = Entity(model="cube", scale=(1.2, 2.2, 0.4), position=(-28, 1.2, -18), color=color.rgb(255, 79, 216), collider="box")
if mira_tex:
    try:
        mira.model = "quad"
        mira.scale = (1.4, 2.4, 1)
        mira.texture = mira_tex
        mira.double_sided = True
    except Exception:
        pass
ml = Entity(position=(-28, 2.8, -18))
Text(text="Mama Mira", parent=ml, scale=8, billboard=True, color=color.pink, origin=(0, 0))

player = FirstPersonController(speed=10, jump_height=1.6, mouse_sensitivity=Vec3(40, 40, 0))
player.position = Vec3(0, 2, 8)
player.cursor.visible = True

CARS = []
car_spots = [(-8, 0.6, 4), (6, 0.6, 4), (-8, 0.6, 10), (6, 0.6, 10), (14, 0.6, -8), (-16, 0.6, 2)]
car_cols = [color.red, color.azure, color.gold, color.white, color.rgb(40, 40, 50), color.lime]
for i, pos in enumerate(car_spots):
    body = Entity(model="cube", scale=(2.2, 0.8, 4.2), position=pos, color=car_cols[i], collider="box")
    Entity(parent=body, model="cube", scale=(0.9, 0.5, 0.5), position=(0, 0.55, 0.2), color=color.rgb(30, 40, 50))
    CARS.append({"ent": body, "speed": 0.0, "yaw": 0.0})

in_car = None
gold = 180
has_gun = False
ammo = 0
hud = Text(text="", position=(-0.86, 0.45), origin=(-0.5, 0.5), scale=1.0, background=True)
talk = Text(text="", position=(-0.5, -0.35), origin=(-0.5, 0.5), scale=1.0, background=True, enabled=False)
toast_t = Text(text="", position=(0, 0.35), origin=(0, 0), scale=1.2, background=True, enabled=False)
toast_until = 0

def toast(msg, dur=2.4):
    global toast_until
    toast_t.text = msg
    toast_t.enabled = True
    toast_until = time.time() + dur

def nearest_car(max_d=4.0):
    best, bd = None, max_d
    for c in CARS:
        d = (c["ent"].position - player.position).length()
        if d < bd:
            best, bd = c, d
    return best

def update():
    global in_car, gold, has_gun, ammo, toast_until
    if toast_t.enabled and time.time() > toast_until:
        toast_t.enabled = False
    if in_car:
        player.visible = False
        player.collider = None
        car = in_car["ent"]
        yaw = in_car["yaw"]
        if held_keys["a"]:
            yaw += 80 * time.dt
        if held_keys["d"]:
            yaw -= 80 * time.dt
        in_car["yaw"] = yaw
        accel = 0
        if held_keys["w"]:
            accel = 18
        if held_keys["s"]:
            accel = -10
        in_car["speed"] += (accel - in_car["speed"] * 2.2) * time.dt
        rad = math.radians(yaw)
        car.rotation_y = yaw
        car.x = car.x + math.sin(rad) * in_car["speed"] * time.dt
        car.z = car.z + math.cos(rad) * in_car["speed"] * time.dt
        player.position = Vec3(car.x, car.y + 1.2, car.z)
        camera.rotation_y = yaw
    else:
        player.visible = True
        if player.collider is None:
            player.collider = "capsule"
    mode = "CAR" if in_car else "ON FOOT"
    gun = "pistol %d" % ammo if has_gun else "unarmed"
    hud.text = "WASD move  |  mouse look  |  E car/talk/buy  |  LMB shoot\n%s  |  gold %d  |  %s" % (mode, gold, gun)
    mira_d = (mira.position - player.position).length()
    gun_d = (Vec3(22, 1, -6) - player.position).length()
    if not in_car and mira_d < 4:
        talk.enabled = True
        talk.text = "Mama Mira: Cool Down's on the board, sugar. [E] talk"
    elif not in_car and gun_d < 5:
        talk.enabled = True
        talk.text = "Gun Hut: 9mm 60g  |  ammo 15g  [E] buy"
    else:
        if talk.text.startswith("Mama Mira") or talk.text.startswith("Gun Hut"):
            talk.enabled = False

def input(key):
    global in_car, gold, has_gun, ammo
    if key == "escape":
        application.quit()
        return
    if key == "e":
        if in_car:
            car = in_car["ent"]
            player.position = Vec3(car.x + 2.5, 2, car.z)
            in_car["speed"] = 0
            in_car = None
            toast("Out of the car.")
            return
        car = nearest_car()
        if car:
            in_car = car
            in_car["yaw"] = car["ent"].rotation_y
            toast("Driving. WASD steer, E to bail.")
            return
        if (mira.position - player.position).length() < 4:
            talk.enabled = True
            talk.text = "Mira: Neon's loud tonight. Cool Down if you want mint. Don't make me wait."
            toast("Mira leans on the stall.")
            return
        if (Vec3(22, 1, -6) - player.position).length() < 5:
            if not has_gun and gold >= 60:
                gold -= 60
                has_gun = True
                ammo += 12
                toast("Bought a 9mm.")
            elif has_gun and gold >= 15:
                gold -= 15
                ammo += 12
                toast("Bought ammo.")
            else:
                toast("Need more gold.")
            return
    if key == "left mouse down" and not in_car:
        if not has_gun:
            toast("No gun. Buy one at Gun Hut.")
            return
        if ammo <= 0:
            toast("Empty.")
            return
        ammo -= 1
        hit = raycast(camera.world_position, camera.forward, distance=40, ignore=(player,))
        toast("Hit." if hit.hit else "Miss.")

Text(text="Clermont · Hwy 50", position=(0, 0.47), origin=(0, 0), scale=1.4, color=color.pink)
toast("WASD to walk. Mouse to look. E for cars.")

if __name__ == "__main__":
    app.run()
