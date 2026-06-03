"""
time_manager.py
Global time state accessible from scripts.
from core.time_manager import Time

Time.delta_time   — seconds since last frame (capped at 0.05)
Time.elapsed      — total seconds since play mode started
Time.frame_count  — frames since play mode started
Time.fps          — smoothed frames per second
Time.time_scale   — multiplier (0 = paused, 0.5 = slow-mo, 1 = normal)
"""

from __future__ import annotations
import time as _time


class _TimeManager:
    def __init__(self):
        self.delta_time: float = 0.0
        self.elapsed: float = 0.0
        self.frame_count: int = 0
        self.fps: float = 0.0
        self.time_scale: float = 1.0

        self._start_time: float = 0.0
        self._last_time: float = 0.0
        self._fps_accum: float = 0.0
        self._fps_frames: int = 0

    def start(self) -> None:
        """Call when play mode begins."""
        now = _time.perf_counter()
        self._start_time = now
        self._last_time = now
        self.elapsed = 0.0
        self.frame_count = 0
        self.fps = 0.0
        self._fps_accum = 0.0
        self._fps_frames = 0

    def tick(self) -> float:
        """
        Call once per game loop iteration.
        Returns the scaled delta_time for this frame.
        """
        now = _time.perf_counter()
        raw_dt = now - self._last_time
        self._last_time = now

        self.delta_time = min(raw_dt, 0.05) * self.time_scale
        self.elapsed += self.delta_time
        self.frame_count += 1

        # FPS smoothed over 0.5s
        self._fps_accum += raw_dt
        self._fps_frames += 1
        if self._fps_accum >= 0.5:
            self.fps = self._fps_frames / self._fps_accum
            self._fps_accum = 0.0
            self._fps_frames = 0

        return self.delta_time

    def stop(self) -> None:
        """Call when play mode ends."""
        self.delta_time = 0.0
        self.time_scale = 1.0


# Singleton
Time = _TimeManager()
