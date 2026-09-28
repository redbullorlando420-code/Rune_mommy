"""Punchy lightweight SFX for Rune Mommy.

Procedural tiny WAVs under assets/sfx/ when missing. Ursina Audio when the
audio backend works; silent stubs otherwise. No huge asset packs.
"""
from __future__ import annotations

import math
import os
import struct
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SFX_DIR = ROOT / 'assets' / 'sfx'

_ENABLED = True
_READY = False
_CACHE = {}
_ENGINE = None
_ENGINE_CAR = None
_LAST_IMPACT_T = 0.0


def audio_wanted() -> bool:
    raw = (os.environ.get('RUNE_MOMMY_AUDIO') or '1').strip().lower()
    return raw not in ('0', 'off', 'false', 'no', 'null')


def _write_wav(path: Path, samples, rate=22050):
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        frames = b''.join(struct.pack('<h', max(-32767, min(32767, int(s)))) for s in samples)
        w.writeframes(frames)


def _tone(freq, dur, rate=22050, vol=0.35, fade=0.02, wave='sine'):
    n = max(1, int(rate * dur))
    fade_n = max(1, int(rate * fade))
    out = []
    for i in range(n):
        t = i / rate
        if wave == 'square':
            v = 1.0 if (int(t * freq * 2) % 2 == 0) else -1.0
        elif wave == 'noise':
            # cheap LCG noise
            v = ((i * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff * 2.0 - 1.0
        else:
            v = math.sin(2.0 * math.pi * freq * t)
        env = 1.0
        if i < fade_n:
            env = i / fade_n
        elif i > n - fade_n:
            env = (n - i) / fade_n
        out.append(v * vol * env * 32767.0)
    return out


def _ensure_assets():
    specs = {
        'ui_beep.wav': lambda: _tone(880, 0.06, vol=0.28, wave='sine'),
        'horn.wav': lambda: (
            _tone(420, 0.22, vol=0.4, wave='square') + _tone(380, 0.18, vol=0.32, wave='square')
        ),
        'impact.wav': lambda: (
            _tone(90, 0.05, vol=0.5, wave='noise') + _tone(55, 0.12, vol=0.45, wave='sine')
        ),
        'impact_heavy.wav': lambda: (
            _tone(70, 0.08, vol=0.55, wave='noise')
            + _tone(40, 0.18, vol=0.5, wave='sine')
            + _tone(120, 0.06, vol=0.25, wave='noise')
        ),
        'engine.wav': lambda: _tone(110, 0.35, vol=0.18, wave='sine')  # short loopable hum
        + _tone(165, 0.35, vol=0.08, wave='sine'),
        'disable.wav': lambda: _tone(180, 0.15, vol=0.35, wave='square') + _tone(90, 0.2, vol=0.3, wave='sine'),
    }
    for name, gen in specs.items():
        path = SFX_DIR / name
        if path.is_file() and path.stat().st_size > 44:
            continue
        try:
            _write_wav(path, gen())
        except Exception as exc:
            print('  sfx write skip:', name, exc)


def boot():
    """Generate stubs + probe Ursina Audio. Safe to call once from Game.setup."""
    global _READY, _ENABLED
    if not audio_wanted():
        _ENABLED = False
        _READY = True
        print('  sfx: disabled (RUNE_MOMMY_AUDIO=0)')
        return
    try:
        _ensure_assets()
    except Exception as exc:
        print('  sfx assets skip:', exc)
    _ENABLED = True
    _READY = True
    # Probe once — failure stays silent stubs
    try:
        clip = _load('ui_beep')
        if clip is None:
            print('  sfx: stubs ready (Audio unavailable — silent)')
        else:
            print('  sfx: ready (engine/impact/horn/ui)')
    except Exception as exc:
        print('  sfx probe skip:', exc)


def _rel(name: str) -> str:
    path = SFX_DIR / f'{name}.wav'
    try:
        return str(path.relative_to(ROOT)).replace('\\', '/')
    except Exception:
        return str(path)


def _load(name: str):
    if not _ENABLED:
        return None
    if name in _CACHE:
        return _CACHE[name]
    try:
        from ursina import Audio
    except Exception:
        _CACHE[name] = None
        return None
    rel = _rel(name)
    abs_path = SFX_DIR / f'{name}.wav'
    clip = None
    for candidate in (rel, str(abs_path)):
        try:
            clip = Audio(candidate, loop=False, autoplay=False)
            if clip is not None:
                break
        except Exception:
            clip = None
    _CACHE[name] = clip
    return clip


def play(name: str, volume=0.55):
    if not _ENABLED:
        return
    clip = _load(name)
    if clip is None:
        return
    try:
        clip.volume = float(volume)
        clip.play()
    except Exception:
        pass


def ui_beep():
    play('ui_beep', 0.4)


def horn():
    play('horn', 0.7)


def impact(speed=10.0):
    global _LAST_IMPACT_T
    import time as _t
    now = _t.time()
    if now - _LAST_IMPACT_T < 0.12:
        return
    _LAST_IMPACT_T = now
    heavy = abs(float(speed)) >= 12.0
    play('impact_heavy' if heavy else 'impact', 0.75 if heavy else 0.55)


def disable_crunch():
    play('disable', 0.65)


def engine_update(car, dt=0.016):
    """Soft engine loop while player drives; pitch/vol from speed."""
    global _ENGINE, _ENGINE_CAR
    if not _ENABLED or car is None:
        engine_stop()
        return
    spd = abs(float(getattr(car, 'speed', 0.0) or 0.0))
    if spd < 0.4 and not getattr(car, '_engine_idle', False):
        # keep a quiet idle while seated
        pass
    try:
        from ursina import Audio
    except Exception:
        return
    if _ENGINE is None or _ENGINE_CAR is not car:
        engine_stop()
        path = _rel('engine')
        abs_path = SFX_DIR / 'engine.wav'
        for candidate in (path, str(abs_path)):
            try:
                _ENGINE = Audio(candidate, loop=True, autoplay=False)
                if _ENGINE is not None:
                    break
            except Exception:
                _ENGINE = None
        _ENGINE_CAR = car
        if _ENGINE is None:
            return
        try:
            _ENGINE.play()
        except Exception:
            _ENGINE = None
            return
    try:
        # Map speed → volume / pitch (Ursina Audio may ignore pitch)
        vol = 0.12 + min(0.45, spd / 28.0 * 0.4)
        _ENGINE.volume = vol
        if hasattr(_ENGINE, 'pitch'):
            _ENGINE.pitch = 0.85 + min(0.55, spd / 26.0 * 0.55)
    except Exception:
        pass


def engine_stop():
    global _ENGINE, _ENGINE_CAR
    if _ENGINE is not None:
        try:
            _ENGINE.stop()
        except Exception:
            pass
    _ENGINE = None
    _ENGINE_CAR = None
