"""
material.py
FIX: __init__ signature normalised — shader is always optional keyword arg.
Added: upload_texture_from_path(), _tex_path for save/load, reload_texture().
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, TYPE_CHECKING

import numpy as np
from core.shader import Shader

if TYPE_CHECKING:
    import moderngl


class Material:
    def __init__(self, shader: Optional["Shader"] = None, name: str = "Material"):
        self.name: str = name
        self.shader: Shader = shader or Shader.from_builtin("mesh")

        self.color: np.ndarray = np.array([1.0, 1.0, 1.0, 1.0], dtype="f4")
        self.use_texture: bool = False
        self.texture: Optional["moderngl.Texture"] = None
        self._tex_path: str = ""

        self.light_dir: np.ndarray = np.array([0.5, -1.0, 0.5], dtype="f4")
        self.light_color: np.ndarray = np.array([1.0, 1.0, 1.0], dtype="f4")
        self.ambient: float = 0.25

        self._extras: dict = {}

    # ── Setters ──────────────────────────────────────────────────────

    def set_color(self, r: float, g: float, b: float, a: float = 1.0) -> None:
        self.color[:] = (r, g, b, a)

    def set_texture(self, texture: "moderngl.Texture") -> None:
        if texture is None:
            self.texture = None
            self.use_texture = False
            self._tex_path = ""
        else:
            self.texture = texture
            self.use_texture = True

    def set_uniform(self, name: str, value) -> None:
        self._extras[name] = value

    # ── Texture from file ────────────────────────────────────────────

    def upload_texture_from_path(self, ctx: "moderngl.Context", path: str) -> bool:
        """Load image → upload to GPU. Returns True on success."""
        try:
            from PIL import Image

            img = Image.open(path).convert("RGBA").transpose(Image.FLIP_TOP_BOTTOM)
            w, h = img.size
            tex = ctx.texture((w, h), 4, data=img.tobytes(), dtype="u1")
            tex.build_mipmaps()
            tex.filter = ctx.LINEAR_MIPMAP_LINEAR, ctx.LINEAR
            self.set_texture(tex)
            self._tex_path = path
            return True
        except Exception as e:
            print(f"[Material] texture load failed '{path}': {e}")
            return False

    def reload_texture(self, ctx: "moderngl.Context") -> bool:
        """Re-upload texture after scene load if _tex_path is set."""
        if self._tex_path and not self.texture:
            return self.upload_texture_from_path(ctx, self._tex_path)
        return False

    # ── GL ───────────────────────────────────────────────────────────

    def compile(self, ctx: "moderngl.Context") -> None:
        if not self.shader.is_compiled():
            self.shader.compile(ctx)

    def bind(
        self, model_matrix: np.ndarray, view: np.ndarray, proj: np.ndarray
    ) -> None:
        prog = self.shader.program
        if prog is None:
            return
        if "u_model" in prog:
            prog["u_model"].write(model_matrix.T.tobytes())
        if "u_view" in prog:
            prog["u_view"].write(view.T.tobytes())
        if "u_proj" in prog:
            prog["u_proj"].write(proj.T.tobytes())
        if "u_color" in prog:
            prog["u_color"].write(self.color.tobytes())
        if "u_use_texture" in prog:
            prog["u_use_texture"].value = self.use_texture
        if "u_light_dir" in prog:
            prog["u_light_dir"].write(self.light_dir.tobytes())
        if "u_light_color" in prog:
            prog["u_light_color"].write(self.light_color.tobytes())
        if "u_ambient" in prog:
            prog["u_ambient"].value = self.ambient
        if self.use_texture and self.texture is not None:
            self.texture.use(location=0)
            if "u_texture" in prog:
                prog["u_texture"].value = 0
        for k, v in self._extras.items():
            self.shader.set(k, v)

    # ── Serialization ────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "shader": self.shader.to_dict(),
            "color": self.color.tolist(),
            "use_texture": self.use_texture,
            "ambient": self.ambient,
            "light_dir": self.light_dir.tolist(),
            "light_color": self.light_color.tolist(),
            "tex_path": self._tex_path,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Material":
        shader = Shader.from_dict(data["shader"])
        mat = cls(shader, name=data.get("name", "Material"))
        mat.color = np.array(data.get("color", [1, 1, 1, 1]), dtype="f4")
        mat.use_texture = data.get("use_texture", False)
        mat.ambient = data.get("ambient", 0.25)
        mat.light_dir = np.array(data.get("light_dir", [0.5, -1, 0.5]), dtype="f4")
        mat.light_color = np.array(data.get("light_color", [1, 1, 1]), dtype="f4")
        mat._tex_path = data.get("tex_path", "")
        return mat

    def __repr__(self) -> str:
        return f"<Material '{self.name}' shader='{self.shader.name}'>"
