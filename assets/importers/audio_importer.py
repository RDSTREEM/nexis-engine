"""
audio_importer.py
Imports audio files via soundfile (no pygame dependency).
Playback uses sounddevice which is Qt-safe (runs in its own thread).

Install: pip install soundfile sounddevice
"""

from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import threading
import numpy as np


@dataclass
class AudioClip:
    name: str
    samples: np.ndarray  # float32, shape (frames, channels)
    sample_rate: int
    channels: int
    duration: float  # seconds
    _play_thread: Optional[threading.Thread] = None

    def play(self, volume: float = 1.0, loop: bool = False) -> None:
        def _run():
            try:
                import sounddevice as sd

                data = self.samples * volume
                if loop:
                    while True:
                        sd.play(data, self.sample_rate, blocking=True)
                else:
                    sd.play(data, self.sample_rate, blocking=True)
            except Exception as e:
                print(f"[Audio] Playback error: {e}")

        self._play_thread = threading.Thread(target=_run, daemon=True)
        self._play_thread.start()

    def stop(self) -> None:
        try:
            import sounddevice as sd

            sd.stop()
        except Exception:
            pass


def import_audio(path: Path) -> AudioClip:
    try:
        import soundfile as sf
    except ImportError:
        raise ImportError(
            "soundfile is required for audio import: pip install soundfile sounddevice"
        )

    samples, sr = sf.read(str(path), dtype="float32", always_2d=True)
    return AudioClip(
        name=path.stem,
        samples=samples,
        sample_rate=sr,
        channels=samples.shape[1],
        duration=len(samples) / sr,
    )
