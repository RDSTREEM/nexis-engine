from __future__ import annotations
from typing import Optional
import numpy as np
import moderngl

from core.component import Component
from core.material import Material
from core.shader import Shader
import core.primitives as prim3d


class MeshRenderer(Component):
    """
    3D mesh rendering component.
    Use set_primitive() for built-in 3D shapes or set_mesh_data() for custom geometry.
    Vertex layout: (pos3, normal3, uv2) = 8 floats per vertex.
    """

    def __init__(self, primitive: str = "cube", material: Optional[Material] = None):
        super().__init__()
        self.primitive = primitive
        self.material = material or Material(Shader.from_builtin("mesh"))
        self._vao: Optional[moderngl.VertexArray] = None
        self._ctx: Optional[moderngl.Context] = None
        self._raw_vertices: Optional[np.ndarray] = None

    def set_primitive(self, name: str) -> None:
        if name not in prim3d.PRIMITIVES:
            raise ValueError(
                f"Unknown 3D primitive '{name}'. Options: {list(prim3d.PRIMITIVES)}"
            )
        self.primitive = name
        self._raw_vertices = None
        self._vao = None

    def set_mesh_data(self, vertices: np.ndarray) -> None:
        """Raw (pos3, normal3, uv2) float32 array."""
        self.primitive = "custom"
        self._raw_vertices = vertices
        self._vao = None

    def _build_vao(self, ctx: moderngl.Context) -> None:
        self._ctx = ctx
        self.material.compile(ctx)

        if self.primitive == "custom" and self._raw_vertices is not None:
            verts = self._raw_vertices
        else:
            verts = prim3d.generate(
                self.primitive if self.primitive in prim3d.PRIMITIVES else "cube"
            )

        vbo = ctx.buffer(verts.tobytes())
        self._vao = ctx.vertex_array(
            self.material.shader.program,
            [(vbo, "3f 3f 2f", "in_position", "in_normal", "in_uv")],
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
                "primitive": self.primitive,
                "material": self.material.to_dict(),
            }
        )
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "MeshRenderer":
        mat = Material.from_dict(data["material"]) if "material" in data else None
        mr = cls(primitive=data.get("primitive", "cube"), material=mat)
        mr.enabled = data.get("enabled", True)
        return mr
