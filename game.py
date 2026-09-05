#!/usr/bin/env python3
"""Rune Mommy  -  Clermont / Hwy 50. Third-person Ursina desktop game.

Windows 11:
    py -3 -m pip install -r requirements.txt
    py -3 game.py
"""
from __future__ import annotations

import json
import math
import os
import random
import sys
import time as pytime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)

from loaders import (
    load_shops, portrait_texture_path, load_npcs, load_mobs, load_items,
    load_oss_items, load_skills, load_progression, load_vehicles,
)
from crowd import spawn_crowd, tick_crowd, spawn_heat_hunter
from traffic import spawn_traffic, tick_traffic
