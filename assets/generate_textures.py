#!/usr/bin/env python3
"""Ensure assets/textures/*.jpg exist (decode from assets/tex_b64 if missing)."""
from __future__ import annotations

def ensure_all() -> list[str]:
    from assets.install_textures import ensure
    return ensure()

if __name__ == "__main__":
    print("wrote:", ", ".join(ensure_all()) or "(already present)")
