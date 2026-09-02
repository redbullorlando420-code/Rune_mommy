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

from loaders import load_shops, portrait_texture_path, load_npcs, load_mobs, load_items

SHAKE_IDS = (
    'shake_bar',
    'steak_n_shake',
    'ritters',
    'brusters',
    'baskin',
    'culvers',
    'five_guys',
    'dairy_queen',
    'mcdonalds',
    'wendys',
)

GAME = None
TEST_SECONDS = 0.0
TEST_T0 = 0.0


def load_json(rel, default=None):
    path = ROOT / rel
    if not path.exists():
        return default
    with path.open(encoding='utf-8') as fh:
        return json.load(fh)


def shake_shop_names():
    data = load_json('data/shops.json', {}) or {}
    names = []
    for shop in data.get('shops', []):
        if shop.get('id') in SHAKE_IDS:
            names.append(shop.get('name', shop['id']))
    return names
