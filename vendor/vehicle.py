"""Kinematic bicycle model. Original impl of the classic public vehicle model."""
from __future__ import annotations

import math


def bicycle_step(
    x,
    z,
    yaw_deg,
    speed,
    steer,
    accel,
    dt,
    vmax=26,
    wheelbase=2.6,
    drag=1.8,
    steer_gain=1.0,
    brake_force=0.0,
    coast_drag=None,
    accel_drag=None,
    handbrake=0.0,
):
    """Advance a 2D bicycle by dt.

    yaw_deg: 0 faces +Z, positive yaw toward +X (Ursina-style).
    steer: -1..1, mapped to a max ~34 deg steer angle (scaled by steer_gain).
    accel: units/s^2 (negative to reverse when already stopped / braking handled via brake_force).
    vmax: forward cap; reverse is capped at 0.4 * vmax.
    steer_gain: scales max steer angle (default 1.0). High speed reduces effective steer.
    brake_force: if > 0, decelerates toward 0 without crossing into reverse.
    coast_drag / accel_drag: optional drag overrides (coast when |accel|<eps and brake_force==0;
        accel_drag used while accelerating). Falls back to `drag`.
    handbrake: 0..1 — extra yaw authority + drag while sliding (Feel pass).
    Returns (x, z, yaw_deg, speed).
    """
    dt = float(dt)
    if dt <= 0:
        return (float(x), float(z), float(yaw_deg), float(speed))

    speed = float(speed)
    vmax = float(vmax)
    accel = float(accel)
    brake_force = max(0.0, float(brake_force or 0.0))
    steer_gain = float(steer_gain if steer_gain is not None else 1.0)
    hb = max(0.0, min(1.0, float(handbrake or 0.0)))

    # Brake toward zero first (does not reverse).
    if brake_force > 0.0 and abs(speed) > 1e-4:
        dec = brake_force * dt
        if abs(speed) <= dec:
            speed = 0.0
        else:
            speed -= math.copysign(dec, speed)
    else:
        speed = speed + accel * dt

    speed = max(-vmax * 0.4, min(vmax, speed))

    # Grip feel: less drag when accelerating, more when coasting.
    coast = float(coast_drag) if coast_drag is not None else float(drag)
    adrag = float(accel_drag) if accel_drag is not None else float(drag) * 0.32
    if hb > 0.0:
        # Handbrake adds slide drag without fully killing steer
        coast = coast + 4.5 * hb
        adrag = adrag + 1.2 * hb
    if brake_force > 0.0 and hb <= 0.0:
        pass  # brake already applied
    elif abs(accel) < 1e-8 or hb > 0.0:
        speed *= max(0.0, 1.0 - coast * dt)
    else:
        speed *= max(0.0, 1.0 - adrag * dt)

    if abs(speed) < 0.04 and abs(accel) < 1e-8 and brake_force <= 0.0 and hb <= 0.0:
        speed = 0.0

    steer = max(-1.0, min(1.0, float(steer)))
    # Speed-sensitive turn: tighter at low speed, less twitch at high speed.
    speed_factor = 1.0 / (1.0 + (abs(speed) / max(1.0, vmax)) * 1.15)
    low_boost = 1.0 + max(0.0, 1.0 - abs(speed) / max(4.0, vmax * 0.25)) * 0.42
    # Handbrake oversteer: unlock yaw at mid/high speed
    hb_yaw = 1.0 + hb * 1.35 * min(1.0, abs(speed) / 10.0)
    effective_steer = steer * steer_gain * speed_factor * low_boost * hb_yaw
    max_steer_deg = 34.0 + 6.0 * hb
    steer_angle = effective_steer * math.radians(max_steer_deg)
    L = max(0.4, float(wheelbase))
    if abs(speed) > 0.04:
        yaw_rate = (speed / L) * math.tan(steer_angle)
        # Extra yaw kick from handbrake (slide)
        if hb > 0.0 and abs(steer) > 0.15:
            yaw_rate += math.radians(70.0) * steer * hb * min(1.0, abs(speed) / 12.0)
        yaw_deg = float(yaw_deg) + math.degrees(yaw_rate) * dt
    else:
        yaw_deg = float(yaw_deg)
    rad = math.radians(yaw_deg)
    x = float(x) + math.sin(rad) * speed * dt
    z = float(z) + math.cos(rad) * speed * dt
    return (x, z, yaw_deg, speed)
