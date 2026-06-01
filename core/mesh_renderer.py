from __future__ import annotations

from typing import Optional, TYPE_CHECKING
import numpy as np
import moderngl

from core.component import Component
from core.material import Material
from core.shader import Shader

if TYPE_CHECKING:
    from core.transform import Transform


# ------------------------------------------------------------------
# Built-in primitive mesh data  (position, normal, uv)
# ------------------------------------------------------------------


def _cube_vertices() -> np.ndarray:
    """Returns a flat f4 array of (pos3, normal3, uv2) per vertex, 36 vertices."""
    # each face: 2 triangles, normal is constant per face
    faces = [
        # pos triples,                           normal,         uvs
        # fmt: off
        ([ (-1,-1, 1),(1,-1, 1),(1,1, 1),(-1,-1, 1),(1,1, 1),(-1,1, 1) ], ( 0, 0, 1)),
        ([ (-1,-1,-1),(1,1,-1),(1,-1,-1),(-1,-1,-1),(-1,1,-1),(1,1,-1) ], ( 0, 0,-1)),
        ([ (-1,-1,-1),(-1,-1, 1),(-1,1, 1),(-1,-1,-1),(-1,1, 1),(-1,1,-1) ], (-1, 0, 0)),
        ([ ( 1,-1,-1),( 1, 1, 1),( 1,-1, 1),( 1,-1,-1),( 1, 1,-1),( 1, 1, 1) ], ( 1, 0, 0)),
        ([ (-1, 1,-1),(-1, 1, 1),( 1, 1, 1),(-1, 1,-1),( 1, 1, 1),( 1, 1,-1) ], ( 0, 1, 0)),
        ([ (-1,-1,-1),( 1,-1, 1),(-1,-1, 1),(-1,-1,-1),( 1,-1,-1),( 1,-1, 1) ], ( 0,-1, 0)),
        # fmt: on
    ]
    uvs = [(0, 0), (1, 0), (1, 1), (0, 0), (1, 1), (0, 1)]
    data = []
    for positions, normal in faces:
        for i, pos in enumerate(positions):
            data.extend([*pos, *normal, *uvs[i]])
    return np.array(data, dtype="f4")


def _quad_vertices() -> np.ndarray:
    """Unit quad in XY plane for sprites."""
    data = [
        # fmt: off
        -0.5,-0.5, 0, 1,
         0.5,-0.5, 1, 1,
         0.5, 0.5, 1, 0,
        -0.5,-0.5, 0, 1,
         0.5, 0.5, 1, 0,
        -0.5, 0.5, 0, 0,
        # fmt: on
    ]
    return np.array(data, dtype="f4")


PRIMITIVE_FACTORIES = {
    "cube": _cube_vertices,
    "quad": _quad_vertices,
}


# ------------------------------------------------------------------
# MeshRenderer
# ------------------------------------------------------------------


class MeshRenderer(Component):
    """
    3D mesh rendering component.
    Attach a Material to control appearance.
    Use set_primitive() for built-in shapes or set_mesh_data() for custom geometry.
    """

    def __init__(self, primitive: str = "cube", material: Optional[Material] = None):
        super().__init__()
        self.primitive: str = primitive
        self.material: Material = material or Material(Shader.from_builtin("mesh"))
        self._vao: Optional[moderngl.VertexArray] = None
        self._ctx: Optional[moderngl.Context] = None

    # ------------------------------------------------------------------

    def set_primitive(self, name: str) -> None:
        if name not in PRIMITIVE_FACTORIES:
            raise ValueError(
                f"Unknown primitive '{name}'. Options: {list(PRIMITIVE_FACTORIES)}"
            )
        self.primitive = name
        self._vao = None  # will be rebuilt next render

    def set_mesh_data(self, vertices: np.ndarray) -> None:
        """
        Provide raw vertex data as f4 array.
        For mesh shader: (pos3, normal3, uv2) = 8 floats per vertex.
        """
        self.primitive = "custom"
        self._raw_vertices = vertices
        self._vao = None

    # ------------------------------------------------------------------

    def _build_vao(self, ctx: moderngl.Context) -> None:
        self._ctx = ctx
        self.material.compile(ctx)

        if self.primitive == "custom" and hasattr(self, "_raw_vertices"):
            verts = self._raw_vertices
        elif self.primitive in PRIMITIVE_FACTORIES:
            verts = PRIMITIVE_FACTORIES[self.primitive]()
        else:
            verts = PRIMITIVE_FACTORIES["cube"]()

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

    # ------------------------------------------------------------------

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
