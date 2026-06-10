"""
debug_draw.py
FIX: Grid is now FINITE (bounded box, not infinite lines).
     grid()    — 3D finite grid with configurable size
     grid_2d() — 2D finite grid with configurable size
     Both stop at ±size units from origin.
"""
from __future__ import annotations
import numpy as np
import moderngl
from typing import Tuple, Optional


_VERT = """
#version 330
in vec3 in_position;
uniform mat4 u_view;
uniform mat4 u_proj;
void main() {
    gl_Position = u_proj * u_view * vec4(in_position, 1.0);
}
"""
_FRAG = """
#version 330
uniform vec4 u_color;
out vec4 out_color;
void main() { out_color = u_color; }
"""


def _mat4(m: np.ndarray) -> bytes:
    return m.astype("f4").T.tobytes()


class DebugDraw:
    def __init__(self):
        self._ctx:    Optional[moderngl.Context] = None
        self._prog:   Optional[moderngl.Program] = None
        self._vbo:    Optional[moderngl.Buffer]  = None
        self._vao:    Optional[moderngl.VertexArray] = None
        self._view:   np.ndarray = np.eye(4, dtype="f4")
        self._proj:   np.ndarray = np.eye(4, dtype="f4")
        self._lines:  list = []   # [(x0,y0,z0, x1,y1,z1), ...]
        self._colors: list = []

    def init_gl(self, ctx: moderngl.Context) -> None:
        self._ctx  = ctx
        self._prog = ctx.program(vertex_shader=_VERT, fragment_shader=_FRAG)
        self._vbo  = ctx.buffer(reserve=1024 * 1024)
        self._vao  = ctx.vertex_array(self._prog, [(self._vbo, "3f", "in_position")])

    def begin(self, view: np.ndarray, proj: np.ndarray) -> None:
        self._view = view
        self._proj = proj
        self._lines.clear()
        self._colors.clear()

    def end(self) -> None:
        if not self._lines:
            return
        verts = np.array(self._lines, dtype="f4").reshape(-1, 3)
        data  = verts.tobytes()
        self._vbo.orphan(max(len(data), 64))
        self._vbo.write(data)
        self._prog["u_view"].write(_mat4(self._view))
        self._prog["u_proj"].write(_mat4(self._proj))
        self._ctx.enable(moderngl.BLEND)
        self._ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA

        i = 0
        for color in self._colors:
            self._prog["u_color"].value = color
            self._vao.render(moderngl.LINES, first=i, vertices=2)
            i += 2
        self._ctx.disable(moderngl.BLEND)

    def line(self, a, b, color=(1, 1, 1, 1)) -> None:
        self._lines.extend([a[0], a[1], a[2], b[0], b[1], b[2]])
        self._colors.append(color)

    # ── FINITE GRID (FIX: was effectively infinite) ───────────────────────────

    def grid(self, size: int = 20, spacing: float = 1.0,
             color=(0.3, 0.3, 0.3, 0.8)) -> None:
        """
        Draw a finite 3D grid on the XZ plane.
        The grid spans from -size to +size in both X and Z.
        Only lines within that range are drawn — no infinite lines.
        """
        half = size * spacing
        steps = range(-size, size + 1)
        for i in steps:
            x = i * spacing
            # Lines parallel to Z
            self.line(( x, 0, -half), ( x, 0,  half), color)
            # Lines parallel to X
            self.line((-half, 0, x),  ( half, 0, x),  color)

        # Bright axis lines (within grid bounds only)
        self.line((-half, 0, 0), (half, 0, 0), (0.8, 0.15, 0.15, 1.0))  # X
        self.line((0, 0, -half), (0, 0, half), (0.15, 0.8, 0.15, 1.0))  # Z

    def grid_2d(self, size: int = 20, spacing: float = 1.0,
                color=(0.3, 0.3, 0.3, 0.8)) -> None:
        """
        Draw a finite 2D grid on the XY plane (for orthographic mode).
        Spans -size..+size in X and Y.
        """
        half = size * spacing
        steps = range(-size, size + 1)
        for i in steps:
            v = i * spacing
            self.line((v, -half, 0), (v,  half, 0), color)
            self.line((-half, v, 0), ( half, v, 0), color)

        # Bright axes
        self.line((-half, 0, 0), (half, 0, 0), (0.8, 0.15, 0.15, 1.0))  # X
        self.line((0, -half, 0), (0,  half, 0), (0.15, 0.8, 0.15, 1.0)) # Y

    # ── Other helpers ─────────────────────────────────────────────────────────

    def axis_gizmo(self, origin=(0, 0, 0), size: float = 1.0) -> None:
        ox, oy, oz = origin
        self.line((ox, oy, oz), (ox+size, oy, oz),      (1, 0.2, 0.2, 1))
        self.line((ox, oy, oz), (ox, oy+size, oz),      (0.2, 1, 0.2, 1))
        self.line((ox, oy, oz), (ox, oy, oz+size),      (0.2, 0.5, 1, 1))

    def selection_box(self, center, half_ext, color=(1, 0.8, 0, 1)) -> None:
        cx, cy, cz = center
        hx, hy, hz = half_ext if hasattr(half_ext, "__iter__") else (half_ext,)*3
        corners = [
            (cx-hx, cy-hy, cz-hz), (cx+hx, cy-hy, cz-hz),
            (cx+hx, cy+hy, cz-hz), (cx-hx, cy+hy, cz-hz),
            (cx-hx, cy-hy, cz+hz), (cx+hx, cy-hy, cz+hz),
            (cx+hx, cy+hy, cz+hz), (cx-hx, cy+hy, cz+hz),
        ]
        edges = [
            (0,1),(1,2),(2,3),(3,0),   # front
            (4,5),(5,6),(6,7),(7,4),   # back
            (0,4),(1,5),(2,6),(3,7),   # sides
        ]
        for a, b in edges:
            self.line(corners[a], corners[b], color)

    def wire_sphere(self, center, radius: float = 1.0,
                    color=(0.5, 0.5, 1, 0.8), segs: int = 16) -> None:
        cx, cy, cz = center
        angles = [2*np.pi*i/segs for i in range(segs+1)]
        for i in range(segs):
            a, b = angles[i], angles[i+1]
            self.line((cx + np.cos(a)*radius, cy + np.sin(a)*radius, cz),
                      (cx + np.cos(b)*radius, cy + np.sin(b)*radius, cz), color)
            self.line((cx + np.cos(a)*radius, cy, cz + np.sin(a)*radius),
                      (cx + np.cos(b)*radius, cy, cz + np.sin(b)*radius), color)

    def ray(self, origin, direction, length: float = 20.0,
            color=(1, 1, 0, 0.8)) -> None:
        d = np.array(direction, dtype="f4")
        n = np.linalg.norm(d)
        if n > 1e-8:
            d /= n
        end = np.array(origin) + d * length
        self.line(origin, end, color)
