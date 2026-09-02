"""Kinematic bicycle model. Original impl of the classic public vehicle model."""
from __future__ import annotations

import math


def bicycle_step(x, z, yaw_deg, speed, steer, accel, dt, vmax=24, wheelbase=2.6, drag=1.8):
    """Advance a 2D bicycle by dt.

    yaw_deg: 0 faces +Z, positive yaw toward +X (Ursina-style).
    steer: -1..1, mapped to a max ~32 deg steer angle.
    accel: units/s^2 (negative to brake / reverse).
    vmax: forward cap; reverse is capped at 0.4 * vmax.
    Returns (x, z, yaw_deg, speed).
    """
    dt = float(dt)
    if dt <= 0:
        return (float(x), float(z), float(yaw_deg), float(speed))
    speed = float(speed) + float(accel) * dt
    vmax = float(vmax)
    speed = max(-vmax * 0.4, min(vmax, speed))
    if abs(float(accel)) < 1e-8:
        speed *= max(0.0, 1.0 - float(drag) * dt)
    steer = max(-1.0, min(1.0, float(steer)))
    steer_angle = steer * math.radians(32.0)
    L = max(0.4, float(wheelbase))
    if abs(speed) > 0.04:
        yaw_rate = (speed / L) * math.tan(steer_angle)
        yaw_deg = float(yaw_deg) + math.degrees(yaw_rate) * dt
    else:
        yaw_deg = float(yaw_deg)
    rad = math.radians(yaw_deg)
    x = float(x) + math.sin(rad) * speed * dt
    z = float(z) + math.cos(rad) * speed * dt
    return (x, z, yaw_deg, speed)
