"""
audio_source.py
AudioSource component — plays AudioClip assets.
Works with the sounddevice/soundfile audio pipeline.
Scriptable: call play(), stop(), pause() from on_update.
"""

from __future__ import annotations
import threading
from typing import Optional, TYPE_CHECKING

import numpy as np

from core.component import Component

if TYPE_CHECKING:
    from assets.importers.audio_importer import AudioClip


class AudioSource(Component):
    def __init__(self):
        super().__init__()
        self.clip: Optional["AudioClip"] = None
        self.volume: float = 1.0
        self.pitch: float = 1.0  # resampling factor
        self.loop: bool = False
        self.play_on_start: bool = False
        self.spatial: bool = False  # future: positional audio
        self._playing: bool = False
        self._paused: bool = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    # ------------------------------------------------------------------

    def set_clip(self, clip: "AudioClip") -> None:
        self.clip = clip

    def on_start(self) -> None:
        if self.play_on_start and self.clip:
            self.play()

    def on_stop(self) -> None:
        self.stop()

    # ------------------------------------------------------------------
    # Playback
    # ------------------------------------------------------------------

    def play(self, from_start: bool = True) -> None:
        if self.clip is None:
            return
        self.stop()
        self._stop_event.clear()
        self._playing = True
        self._paused = False
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._playing:
            self._stop_event.set()
            try:
                import sounddevice as sd

                sd.stop()
            except Exception:
                pass
        self._playing = False
        self._paused = False

    def pause(self) -> None:
        if not self._playing:
            return
        self._paused = not self._paused
        try:
            import sounddevice as sd

            if self._paused:
                sd.stop()
        except Exception:
            pass

    @property
    def is_playing(self) -> bool:
        return self._playing and not self._paused

    # ------------------------------------------------------------------

    def _run(self) -> None:
        try:
            import sounddevice as sd

            samples = self.clip.samples * self.clip

            # pitch shift via resampling
            if abs(self.pitch - 1.0) > 0.01:
                import numpy as np

                orig_len = len(self.clip.samples)
                new_len = int(orig_len / self.pitch)
                indices = np.linspace(0, orig_len - 1, new_len).astype(int)
                samples = self.clip.samples[indices]

            samples = samples * self.volume

            while not self._stop_event.is_set():
                sd.play(samples, self.clip.sample_rate, blocking=True)
                if not self.loop or self._stop_event.is_set():
                    break

        except Exception as e:
            print(f"[AudioSource] Playback error: {e}")
        finally:
            self._playing = False

    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update(
            {
                "volume": self.volume,
                "pitch": self.pitch,
                "loop": self.loop,
                "play_on_start": self.play_on_start,
                "spatial": self.spatial,
                "clip_path": self.clip.name if self.clip else "",
            }
        )
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "AudioSource":
        a = cls()
        a.enabled = data.get("enabled", True)
        a.volume = data.get("volume", 1.0)
        a.pitch = data.get("pitch", 1.0)
        a.loop = data.get("loop", False)
        a.play_on_start = data.get("play_on_start", False)
        a.spatial = data.get("spatial", False)
        return a
