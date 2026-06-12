from __future__ import annotations
from typing import Optional
import numpy as np
import moderngl

from core.component import Component
from core.material import Material
from core.shader import Shader
import core.primitives_2d as prim2d


class SpriteRenderer(Component):
    def __init__(self, material: Optional[Material] = None, shape: str = "square"):
        super().__init__()
        shader = Shader.from_builtin("sprite")
        self.material = material or Material(shader=shader, name="SpriteMaterial")
        self.shape = shape
        self._vao: Optional[moderngl.VertexArray] = None
        self._ctx: Optional[moderngl.Context] = None
        self.size = np.array([1.0, 1.0], dtype="f4")
        self.flip_x = False
        self.flip_y = False

    def set_texture(self, texture: moderngl.Texture) -> None:
        self.material.set_texture(texture)

    def set_color(self, r: float, g: float, b: float, a: float = 1.0) -> None:
        self.material.set_color(r, g, b, a)

    def set_size(self, w: float, h: float) -> None:
        self.size[:] = (w, h)
        self._vao = None

    def set_shape(self, shape: str) -> None:
        if shape not in prim2d.PRIMITIVES_2D:
            raise ValueError(
                f"Unknown 2D shape '{shape}'. Options: {list(prim2d.PRIMITIVES_2D)}"
            )
        self.shape = shape
        self._vao = None

    def _build_vao(self, ctx: moderngl.Context) -> None:
        self._ctx = ctx
        self.material.compile(ctx)
        self.material.reload_texture(ctx)
        verts = prim2d.generate_2d(self.shape).reshape(-1, 4).copy()
        verts[:, 0] *= self.size[0]
        verts[:, 1] *= self.size[1]
        if self.flip_x:
            verts[:, 2] = 1.0 - verts[:, 2]
        if self.flip_y:
            verts[:, 3] = 1.0 - verts[:, 3]
        vbo = ctx.buffer(verts.tobytes())
        self._vao = ctx.vertex_array(
            self.material.shader.program,
            [(vbo, "2f 2f", "in_position", "in_uv")],
        )

    def render(self, ctx: moderngl.Context, view: np.ndarray, proj: np.ndarray) -> None:
        if not self.enabled or self.entity is None:
            return
        if self._vao is None or self._ctx is not ctx:
            self._build_vao(ctx)
        model = self.entity.transform.matrix
        self.material.bind(model, view, proj)
        self._vao.render(moderngl.TRIANGLES)

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update(
            {
                "material": self.material.to_dict(),
                "shape": self.shape,
                "size": self.size.tolist(),
                "flip_x": self.flip_x,
                "flip_y": self.flip_y,
            }
        )
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "SpriteRenderer":
        mat = Material.from_dict(data["material"]) if "material" in data else None
        sr = cls(material=mat, shape=data.get("shape", "square"))
        sr.enabled = data.get("enabled", True)
        sr.size = np.array(data.get("size", [1, 1]), dtype="f4")
        sr.flip_x = data.get("flip_x", False)
        sr.flip_y = data.get("flip_y", False)
        return sr


# ── Shape2DRenderer ─────────────────────────────────────────────────────────

_SHAPE_VERT = """
#version 330
in vec2 in_position;
uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_proj;
void main() {
    gl_Position = u_proj * u_view * u_model * vec4(in_position, 0.0, 1.0);
}
"""

_SHAPE_FRAG = """
#version 330
uniform vec4 u_color;
out vec4 f_color;
void main() { f_color = u_color; }
"""


class Shape2DRenderer(Component):
    """Solid-colour 2D shape — no texture, no lighting."""

    def __init__(self, shape: str = "square", color: tuple = (1.0, 1.0, 1.0, 1.0)):
        super().__init__()
        self.shape = shape
        self.color = np.array(color, dtype="f4")
        self.size = np.array([1.0, 1.0], dtype="f4")
        self._vao: Optional[moderngl.VertexArray] = None
        self._prog: Optional[moderngl.Program] = None
        self._ctx: Optional[moderngl.Context] = None

    def set_shape(self, shape: str) -> None:
        if shape not in prim2d.PRIMITIVES_2D:
            raise ValueError(f"Unknown 2D shape '{shape}'.")
        self.shape = shape
        self._vao = None

    def set_color(self, r: float, g: float, b: float, a: float = 1.0) -> None:
        self.color[:] = (r, g, b, a)

    def set_size(self, w: float, h: float) -> None:
        self.size[:] = (w, h)
        self._vao = None

    def _build(self, ctx: moderngl.Context) -> None:
        self._ctx = ctx
        self._prog = ctx.program(vertex_shader=_SHAPE_VERT, fragment_shader=_SHAPE_FRAG)
        verts = prim2d.generate_2d(self.shape).reshape(-1, 4).copy()
        verts[:, 0] *= self.size[0]
        verts[:, 1] *= self.size[1]
        xy = np.ascontiguousarray(verts[:, :2])
        vbo = ctx.buffer(xy.tobytes())
        self._vao = ctx.vertex_array(self._prog, [(vbo, "2f", "in_position")])

    def render(self, ctx: moderngl.Context, view: np.ndarray, proj: np.ndarray) -> None:
        if not self.enabled or self.entity is None:
            return
        if self._vao is None or self._ctx is not ctx:
            self._build(ctx)
        model = self.entity.transform.matrix
        self._prog["u_model"].write(model.T.tobytes())
        self._prog["u_view"].write(view.T.tobytes())
        self._prog["u_proj"].write(proj.T.tobytes())
        self._prog["u_color"].write(self.color.tobytes())
        self._vao.render(moderngl.TRIANGLES)

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update(
            {
                "shape": self.shape,
                "color": self.color.tolist(),
                "size": self.size.tolist(),
            }
        )
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Shape2DRenderer":
        s = cls(
            shape=data.get("shape", "square"), color=data.get("color", [1, 1, 1, 1])
        )
        s.enabled = data.get("enabled", True)
        s.size = np.array(data.get("size", [1, 1]), dtype="f4")
        return s
