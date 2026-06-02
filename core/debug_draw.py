"""
debug_draw.py
Renders lines, gizmos, grid, axis arrows, and bounding boxes.
All drawing is immediate-mode style — call begin(), submit geometry, end().
Uses a single line-shader shared across all draw calls.
"""

from __future__ import annotations
from typing import Optional
import numpy as np
import moderngl

_LINE_VERT = """
#version 330
in vec3 in_pos;
in vec3 in_col;
uniform mat4 u_view;
uniform mat4 u_proj;
out vec3 v_col;
void main() {
    gl_Position = u_proj * u_view * vec4(in_pos, 1.0);
    v_col = in_col;
}
"""

_LINE_FRAG = """
#version 330
in vec3 v_col;
out vec4 f_color;
void main() { f_color = vec4(v_col, 1.0); }
"""

# colours
RED = (1.0, 0.2, 0.2)
GREEN = (0.2, 1.0, 0.2)
BLUE = (0.2, 0.4, 1.0)
YELLOW = (1.0, 1.0, 0.2)
WHITE = (1.0, 1.0, 1.0)
GREY = (0.4, 0.4, 0.4)
ORANGE = (1.0, 0.5, 0.1)


class DebugDraw:
    """
    Usage (inside paintGL, after scene render):
        dd.begin(view, proj)
        dd.line((0,0,0), (1,0,0), RED)
        dd.axis_gizmo((0,0,0), size=1)
        dd.grid()
        dd.end()
    """

    MAX_VERTS = 65536

    def __init__(self):
        self._ctx: Optional[moderngl.Context] = None
        self._prog: Optional[moderngl.Program] = None
        self._vbo: Optional[moderngl.Buffer] = None
        self._vao: Optional[moderngl.VertexArray] = None
        self._buf: np.ndarray = np.zeros((self.MAX_VERTS, 6), dtype="f4")
        self._count: int = 0
        self._view: Optional[np.ndarray] = None
        self._proj: Optional[np.ndarray] = None

    # ------------------------------------------------------------------
    # GL init  (call once after context is available)
    # ------------------------------------------------------------------

    def init_gl(self, ctx: moderngl.Context) -> None:
        self._ctx = ctx
        self._prog = ctx.program(vertex_shader=_LINE_VERT, fragment_shader=_LINE_FRAG)
        self._vbo = ctx.buffer(reserve=self.MAX_VERTS * 6 * 4, dynamic=True)
        self._vao = ctx.vertex_array(
            self._prog,
            [(self._vbo, "3f 3f", "in_pos", "in_col")],
        )

    # ------------------------------------------------------------------
    # Frame API
    # ------------------------------------------------------------------

    def begin(self, view: np.ndarray, proj: np.ndarray) -> None:
        self._count = 0
        self._view = view
        self._proj = proj

    def end(self) -> None:
        if self._count == 0 or self._ctx is None:
            return
        data = self._buf[: self._count]
        self._vbo.write(data.tobytes())
        self._prog["u_view"].write(self._view.T.tobytes())
        self._prog["u_proj"].write(self._proj.T.tobytes())
        self._ctx.disable(moderngl.DEPTH_TEST)
        self._vao.render(moderngl.LINES, vertices=self._count)
        self._ctx.enable(moderngl.DEPTH_TEST)

    # ------------------------------------------------------------------
    # Primitives
    # ------------------------------------------------------------------

    def line(self, a, b, color=WHITE) -> None:
        self._push(a, color)
        self._push(b, color)

    def axis_gizmo(self, origin=(0, 0, 0), size: float = 1.0) -> None:
        o = np.array(origin, dtype="f4")
        self.line(o, o + (size, 0, 0), RED)
        self.line(o, o + (0, size, 0), GREEN)
        self.line(o, o + (0, 0, size), BLUE)

    def wire_box(self, center, half_extents, color=WHITE) -> None:
        cx, cy, cz = center
        hx, hy, hz = half_extents
        corners = [
            (cx - hx, cy - hy, cz - hz),
            (cx + hx, cy - hy, cz - hz),
            (cx + hx, cy + hy, cz - hz),
            (cx - hx, cy + hy, cz - hz),
            (cx - hx, cy - hy, cz + hz),
            (cx + hx, cy - hy, cz + hz),
            (cx + hx, cy + hy, cz + hz),
            (cx - hx, cy + hy, cz + hz),
        ]
        edges = [
            (0, 1),
            (1, 2),
            (2, 3),
            (3, 0),
            (4, 5),
            (5, 6),
            (6, 7),
            (7, 4),
            (0, 4),
            (1, 5),
            (2, 6),
            (3, 7),
        ]
        for a, b in edges:
            self.line(corners[a], corners[b], color)

    def wire_sphere(
        self, center, radius: float, color=WHITE, segments: int = 16
    ) -> None:
        import math

        cx, cy, cz = center
        for plane in range(3):
            prev = None
            for i in range(segments + 1):
                a = 2 * math.pi * i / segments
                if plane == 0:
                    pt = (cx + math.cos(a) * radius, cy + math.sin(a) * radius, cz)
                elif plane == 1:
                    pt = (cx, cy + math.cos(a) * radius, cz + math.sin(a) * radius)
                else:
                    pt = (cx + math.cos(a) * radius, cy, cz + math.sin(a) * radius)
                if prev is not None:
                    self.line(prev, pt, color)
                prev = pt

    def grid(self, size: int = 10, spacing: float = 1.0, color=GREY) -> None:
        half = size * spacing
        for i in range(-size, size + 1):
            t = i * spacing
            self.line((-half, 0, t), (half, 0, t), color)
            self.line((t, 0, -half), (t, 0, half), color)

    def grid_2d(self, size: int = 10, spacing: float = 1.0, color=GREY) -> None:
        """For 2D mode — draws on XY plane."""
        half = size * spacing
        for i in range(-size, size + 1):
            t = i * spacing
            self.line((-half, t, 0), (half, t, 0), color)
            self.line((t, -half, 0), (t, half, 0), color)

    def selection_box(self, center, half_extents) -> None:
        """Orange wire box drawn around selected entity."""
        self.wire_box(center, half_extents, ORANGE)

    def ray(self, origin, direction, length: float = 100.0, color=YELLOW) -> None:
        o = np.array(origin, dtype="f4")
        d = np.array(direction, dtype="f4")
        norm = np.linalg.norm(d)
        if norm > 1e-6:
            d = d / norm
        self.line(o, o + d * length, color)

    # ------------------------------------------------------------------

    def _push(self, pos, color) -> None:
        if self._count >= self.MAX_VERTS:
            return
        self._buf[self._count, :3] = pos
        self._buf[self._count, 3:] = color
        self._count += 1
