from __future__ import annotations

from typing import Optional
import numpy as np
import moderngl

from core.component import Component
from core.material import Material
from core.shader import Shader

_QUAD = np.array(
    [
        # fmt: off
    -0.5, -0.5,  0.0, 1.0,
     0.5, -0.5,  1.0, 1.0,
     0.5,  0.5,  1.0, 0.0,
    -0.5, -0.5,  0.0, 1.0,
     0.5,  0.5,  1.0, 0.0,
    -0.5,  0.5,  0.0, 0.0,
        # fmt: on
    ],
    dtype="f4",
)


class SpriteRenderer(Component):
    """
    2D sprite rendering component.
    Uses the sprite shader (no lighting, just texture * color).
    Assign a moderngl Texture via set_texture().
    """

    def __init__(self, material: Optional[Material] = None):
        super().__init__()
        shader = Shader.from_builtin("sprite")
        self.material = material or Material(shader, name="SpriteMaterial")
        self._vao: Optional[moderngl.VertexArray] = None
        self._ctx: Optional[moderngl.Context] = None
        # pixel-space size multiplier (1 = 1 world unit)
        self.size = np.array([1.0, 1.0], dtype="f4")
        # which region of the texture to show (x, y, w, h) in 0-1 UV space
        self.uv_rect = np.array([0.0, 0.0, 1.0, 1.0], dtype="f4")
        self.flip_x = False
        self.flip_y = False

    # ------------------------------------------------------------------

    def set_texture(self, texture: moderngl.Texture) -> None:
        self.material.set_texture(texture)

    def set_color(self, r: float, g: float, b: float, a: float = 1.0) -> None:
        self.material.set_color(r, g, b, a)

    def set_size(self, w: float, h: float) -> None:
        self.size[:] = (w, h)

    # ------------------------------------------------------------------

    def _build_vao(self, ctx: moderngl.Context) -> None:
        self._ctx = ctx
        self.material.compile(ctx)
        vbo = ctx.buffer(_QUAD.tobytes())
        self._vao = ctx.vertex_array(
            self.material.shader.program,
            [(vbo, "2f 2f", "in_position", "in_uv")],
        )

    def render(self, ctx: moderngl.Context, view: np.ndarray, proj: np.ndarray) -> None:
        if not self.enabled or self.entity is None:
            return
        if self._vao is None or self._ctx is not ctx:
            self._build_vao(ctx)

        # bake size into model matrix
        model = self.entity.transform.matrix.copy()
        model[0, 0] *= self.size[0]
        model[1, 1] *= self.size[1]

        self.material.bind(model, view, proj)
        self._vao.render(moderngl.TRIANGLES)

    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update(
            {
                "material": self.material.to_dict(),
                "size": self.size.tolist(),
                "uv_rect": self.uv_rect.tolist(),
                "flip_x": self.flip_x,
                "flip_y": self.flip_y,
            }
        )
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "SpriteRenderer":
        mat = Material.from_dict(data["material"]) if "material" in data else None
        sr = cls(material=mat)
        sr.enabled = data.get("enabled", True)
        sr.size = np.array(data.get("size", [1, 1]), dtype="f4")
        sr.uv_rect = np.array(data.get("uv_rect", [0, 0, 1, 1]), dtype="f4")
        sr.flip_x = data.get("flip_x", False)
        sr.flip_y = data.get("flip_y", False)
        return sr
