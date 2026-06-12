from __future__ import annotations
from typing import Callable, Any
import traceback


class _EventSystem:
    def __init__(self):
        self._listeners: dict[str, list[Callable]] = {}

    def on(self, event: str, callback: Callable) -> None:
        """Subscribe to an event."""
        if event not in self._listeners:
            self._listeners[event] = []
        if callback not in self._listeners[event]:
            self._listeners[event].append(callback)

    def off(self, event: str, callback: Callable) -> None:
        """Unsubscribe from an event."""
        if event in self._listeners:
            self._listeners[event] = [
                cb for cb in self._listeners[event] if cb is not callback
            ]

    def emit(self, event: str, data: Any = None) -> None:
        """Emit an event to all subscribers."""
        for cb in list(self._listeners.get(event, [])):
            try:
                cb(data)
            except Exception:
                print(
                    f"[Events] Error in handler for '{event}':\n"
                    f"{traceback.format_exc()}"
                )

    def clear(self) -> None:
        """Remove all listeners. Called on play mode stop."""
        self._listeners.clear()

    def clear_event(self, event: str) -> None:
        self._listeners.pop(event, None)

    def has_listeners(self, event: str) -> bool:
        return bool(self._listeners.get(event))


# Singleton
Events = _EventSystem()
