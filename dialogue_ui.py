"""Clickable dialogue choice helpers (Ursina Buttons + number keys).

game.py builds panel_choices as Buttons (8 slots). open_panel wires on_click
to _pick_choice; input handles keys 1-8 while ui_open.
This module documents the contract and offers a rebuild helper if needed.
"""
from __future__ import annotations

MAX_CHOICES = 8


def wire_choice_clicks(panel_choices, pick_fn, choices):
    """Enable slots, set labels '1  …', bind on_click → pick_fn(i)."""
    shown = list(choices)[: len(panel_choices)]
    for i, slot in enumerate(panel_choices):
        if i < len(shown):
            slot.enabled = True
            slot.text = f'{i + 1}  {shown[i][0]}'
            slot.on_click = (lambda idx=i: pick_fn(idx))
        else:
            slot.enabled = False
            slot.text = ''
            try:
                slot.on_click = None
            except Exception:
                pass


def clear_choice_clicks(panel_choices):
    for slot in panel_choices:
        slot.enabled = False
        try:
            slot.on_click = None
        except Exception:
            pass


def key_is_choice(key: str) -> int | None:
    """Return 0-based index if key is '1'..'8', else None."""
    if key in ('1', '2', '3', '4', '5', '6', '7', '8'):
        return int(key) - 1
    return None
