"""Tiny finite state machine. Original, for NPC brains."""
from __future__ import annotations


class FSM:
    """Named states with optional enter / update / exit callbacks.

    add(name, on_enter=None, on_update=None, on_exit=None)
    set(name)
    update(dt, ctx)
    """

    def __init__(self, initial=None):
        self.states = {}
        self.current = initial
        self._entered = False

    def add(self, name, on_enter=None, on_update=None, on_exit=None):
        self.states[name] = {
            "on_enter": on_enter,
            "on_update": on_update,
            "on_exit": on_exit,
        }
        if self.current is None:
            self.current = name
        return self

    def set(self, name):
        if name not in self.states:
            raise KeyError("unknown state %r" % (name,))
        if name == self.current and self._entered:
            return
        prev = self.states.get(self.current) if self._entered else None
        if prev and prev["on_exit"]:
            prev["on_exit"]()
        self.current = name
        self._entered = True
        st = self.states[name]
        if st["on_enter"]:
            st["on_enter"]()

    def update(self, dt, ctx=None):
        if not self._entered and self.current in self.states:
            self.set(self.current)
        st = self.states.get(self.current)
        if st and st["on_update"]:
            st["on_update"](dt, ctx)
