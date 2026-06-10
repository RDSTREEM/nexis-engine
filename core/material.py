"""
material.py
Fixed material system.
- set_texture() now accepts either a ModernGL Texture object or a raw PIL/numpy
  image, uploading to GPU automatically when a context is available.
- use_texture flag is set/cleared properly.
- to_dict/from_dict preserve texture path for save/load.
"""
from __future__ import annotations
from pathlib import Path
from typing import Optional, TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import moderngl


class Material:
    def __init__(self):
        self.color:       np.ndarray = np.array([1.0, 1.0, 1.0, 1.0], dtype="f4")
        self.ambient:     float      = 0.3
        self.texture:     Optional["moderngl.Texture"] = None
        self.use_texture: bool       = False
        self._tex_path:   str        = ""   # for serialization

    # ------------------------------------------------------------------

    def set_color(self, r: float, g: float, b: float, a: float = 1.0) -> None:
        self.color[:] = [r, g, b, a]

    def set_texture(self, texture: "moderngl.Texture") -> None:
        """Assign a GPU texture. Pass None to clear."""
        if texture is None:
            self.texture     = None
            self.use_texture = False
            self._tex_path   = ""
        else:
            self.texture     = texture
            self.use_texture = True

    def set_texture_path(self, path: str) -> None:
        """Record path for save/load — actual upload done by inspector/importer."""
        self._tex_path = path

    def upload_texture_from_path(self, ctx: "moderngl.Context", path: str) -> bool:
        """
        Attempt to load an image file and upload to GPU.
        Returns True on success.
        """
        try:
            from PIL import Image
            img = Image.open(path).convert("RGBA")
            w, h = img.size
            data = img.tobytes()
            tex  = ctx.texture((w, h), 4, data)
            tex.build_mipmaps()
            tex.filter = ctx.LINEAR_MIPMAP_LINEAR, ctx.LINEAR
            self.set_texture(tex)
            self._tex_path = path
            return True
        except Exception as e:
            print(f"[Material] Could not load texture '{path}': {e}")
            return False

    def bind(self, prog: "moderngl.Program", unit: int = 0) -> None:
        """Bind this material's uniforms to a shader program."""
        if "u_color" in prog:
            prog["u_color"].value = tuple(self.color)
        if "u_ambient" in prog:
            prog["u_ambient"].value = float(self.ambient)
        if "u_use_texture" in prog:
            prog["u_use_texture"].value = int(self.use_texture and self.texture is not None)
        if self.use_texture and self.texture is not None:
            self.texture.use(location=unit)
            if "u_texture" in prog:
                prog["u_texture"].value = unit

    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "color":       self.color.tolist(),
            "ambient":     self.ambient,
            "use_texture": self.use_texture,
            "tex_path":    self._tex_path,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Material":
        m = cls()
        m.color[:]    = data.get("color", [1, 1, 1, 1])
        m.ambient     = data.get("ambient", 0.3)
        m.use_texture = data.get("use_texture", False)
        m._tex_path   = data.get("tex_path", "")
        return m

    def reload_texture(self, ctx: "moderngl.Context") -> None:
        """Re-upload texture after scene load if path is set."""
        if self._tex_path and not self.texture:
            self.upload_texture_from_path(ctx, self._tex_path)
