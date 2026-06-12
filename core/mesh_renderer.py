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
    Vertex layout: (pos3, normal3, uv2) = 8 floats per vertex.
    """

    def __init__(self, primitive: str = "cube", material: Optional[Material] = None):
        super().__init__()
        self.primitive = primitive
        # FIX: was Material(Shader.from_builtin("mesh")) which failed when
        # Material.__init__ had been patched to take no positional args.
        # Now: always use keyword arg.
        self.material = material or Material(shader=Shader.from_builtin("mesh"))
        self._vao: Optional[moderngl.VertexArray] = None
        self._ctx: Optional[moderngl.Context] = None
        self._raw_vertices: Optional[np.ndarray] = None

    # ── API ──────────────────────────────────────────────────────────

    def set_primitive(self, name: str) -> None:
        if name not in prim3d.PRIMITIVES:
            raise ValueError(
                f"Unknown 3D primitive '{name}'. Options: {list(prim3d.PRIMITIVES)}"
            )
        self.primitive = name
        self._raw_vertices = None
        self._vao = None

    def set_mesh_data(self, vertices: np.ndarray) -> None:
        self.primitive = "custom"
        self._raw_vertices = vertices
        self._vao = None

    # ── GL ───────────────────────────────────────────────────────────

    def _build_vao(self, ctx: moderngl.Context) -> None:
        self._ctx = ctx
        self.material.compile(ctx)
        # Restore texture if it was saved to disk but not yet uploaded
        self.material.reload_texture(ctx)

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

    # ── Serialization ─────────────────────────────────────────────────

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({"primitive": self.primitive, "material": self.material.to_dict()})
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "MeshRenderer":
        mat = Material.from_dict(data["material"]) if "material" in data else None
        mr = cls(primitive=data.get("primitive", "cube"), material=mat)
        mr.enabled = data.get("enabled", True)
        return mr
