"""
texture_importer.py
Imports image files via Pillow → returns raw RGBA bytes + size.
The moderngl Texture is created lazily when the GL context is available.
"""

from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass
import numpy as np
import moderngl


@dataclass
class TextureData:
    """Raw pixel data — converted to moderngl.Texture in upload_to_gpu()."""

    width: int
    height: int
    channels: int  # 3 = RGB, 4 = RGBA
    pixels: bytes
    name: str = ""

    def upload_to_gpu(self, ctx) -> "moderngl.Texture":

        fmt = "rgba8" if self.channels == 4 else "rgb8"
        comp = self.channels
        tex = ctx.texture((self.width, self.height), comp, data=self.pixels, dtype="u1")
        tex.build_mipmaps()
        tex.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)
        tex.anisotropy = 16.0
        return tex


def import_texture(path: Path) -> TextureData:
    try:
        from PIL import Image
    except ImportError:
        raise ImportError("Pillow is required for texture import: pip install Pillow")

    img = Image.open(str(path)).convert("RGBA")
    img = img.transpose(Image.FLIP_TOP_BOTTOM)  # OpenGL UV origin
    w, h = img.size
    return TextureData(
        width=w,
        height=h,
        channels=4,
        pixels=img.tobytes(),
        name=path.stem,
    )
