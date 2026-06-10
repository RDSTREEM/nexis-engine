"""
debug_draw.py
FIX: Grid is now infinite — it scrolls with the camera by snapping
     the grid origin to the nearest grid cell under the camera.
     This gives the illusion of an infinite grid without drawing
     thousands of lines.
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

RED = (1.0, 0.2, 0.2)
GREEN = (0.2, 1.0, 0.2)
BLUE = (0.2, 0.4, 1.0)
YELLOW = (1.0, 1.0, 0.2)
WHITE = (1.0, 1.0, 1.0)
GREY = (0.32, 0.32, 0.32)
ORANGE = (1.0, 0.5, 0.1)


class DebugDraw:
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

    def init_gl(self, ctx: moderngl.Context) -> None:
        self._ctx = ctx
        self._prog = ctx.program(vertex_shader=_LINE_VERT, fragment_shader=_LINE_FRAG)
        self._vbo = ctx.buffer(reserve=self.MAX_VERTS * 6 * 4, dynamic=True)
        self._vao = ctx.vertex_array(
            self._prog, [(self._vbo, "3f 3f", "in_pos", "in_col")]
        )

    def begin(self, view: np.ndarray, proj: np.ndarray) -> None:
        self._count = 0
        self._view = view
        self._proj = proj

    def end(self) -> None:
        if self._count == 0 or self._ctx is None:
            return
        self._vbo.write(self._buf[: self._count].tobytes())
        self._prog["u_view"].write(self._view.T.tobytes())
        self._prog["u_proj"].write(self._proj.T.tobytes())
        self._ctx.disable(moderngl.DEPTH_TEST)
        self._vao.render(moderngl.LINES, vertices=self._count)
        self._ctx.enable(moderngl.DEPTH_TEST)

    def line(self, a, b, color=WHITE) -> None:
        self._push(a, color)
        self._push(b, color)

    # ── INFINITE GRID — snaps origin to camera, giving infinite feel ──────

    def grid(
        self, size: int = 20, spacing: float = 1.0, color=GREY, camera_pos=None
    ) -> None:
        """
        3D grid on XZ plane.  `size` lines in each direction from the
        snapped camera position → looks infinite as camera moves.
        """
        # Extract camera XZ position from view matrix (inverse translation)
        if camera_pos is not None:
            cx, cz = camera_pos[0], camera_pos[2]
        elif self._view is not None:
            inv = np.linalg.inv(self._view)
            cx, cz = float(inv[0, 3]), float(inv[2, 3])
        else:
            cx, cz = 0.0, 0.0

        # Snap to nearest grid cell
        ox = round(cx / spacing) * spacing
        oz = round(cz / spacing) * spacing
        half = size * spacing

        for i in range(-size, size + 1):
            t = i * spacing
            x = ox + t
            z = oz + t
            # lines parallel to Z
            self.line((x, 0, oz - half), (x, 0, oz + half), color)
            # lines parallel to X
            self.line((ox - half, 0, z), (ox + half, 0, z), color)

        # Bright world-axes (unsnapped — always at 0)
        self.line((-half + ox, 0, 0), (half + ox, 0, 0), RED)
        self.line((0, 0, -half + oz), (0, 0, half + oz), BLUE)

    def grid_2d(
        self, size: int = 20, spacing: float = 1.0, color=GREY, camera_pos=None
    ) -> None:
        """
        2D grid on XY plane — infinite scrolling version.
        """
        if camera_pos is not None:
            cx, cy = camera_pos[0], camera_pos[1]
        elif self._view is not None:
            inv = np.linalg.inv(self._view)
            cx, cy = float(inv[0, 3]), float(inv[1, 3])
        else:
            cx, cy = 0.0, 0.0

        ox = round(cx / spacing) * spacing
        oy = round(cy / spacing) * spacing
        half = size * spacing

        for i in range(-size, size + 1):
            t = i * spacing
            self.line((ox + t, oy - half, 0), (ox + t, oy + half, 0), color)
            self.line((ox - half, oy + t, 0), (ox + half, oy + t, 0), color)

        self.line((-half + ox, 0, 0), (half + ox, 0, 0), RED)
        self.line((0, -half + oy, 0), (0, half + oy, 0), GREEN)

    # ── Other helpers (unchanged) ─────────────────────────────────────────

    def axis_gizmo(self, origin=(0, 0, 0), size: float = 1.0) -> None:
        o = np.array(origin, dtype="f4")
        self.line(o, o + (size, 0, 0), RED)
        self.line(o, o + (0, size, 0), GREEN)
        self.line(o, o + (0, 0, size), BLUE)

    def wire_box(self, center, half_extents, color=WHITE) -> None:
        cx, cy, cz = center
        hx, hy, hz = half_extents
        c = [
            (cx - hx, cy - hy, cz - hz),
            (cx + hx, cy - hy, cz - hz),
            (cx + hx, cy + hy, cz - hz),
            (cx - hx, cy + hy, cz - hz),
            (cx - hx, cy - hy, cz + hz),
            (cx + hx, cy - hy, cz + hz),
            (cx + hx, cy + hy, cz + hz),
            (cx - hx, cy + hy, cz + hz),
        ]
        for a, b in [
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
        ]:
            self.line(c[a], c[b], color)

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
                if prev:
                    self.line(prev, pt, color)
                prev = pt

    def selection_box(self, center, half_extents) -> None:
        self.wire_box(center, half_extents, ORANGE)

    def ray(self, origin, direction, length: float = 100.0, color=YELLOW) -> None:
        o = np.array(origin, dtype="f4")
        d = np.array(direction, dtype="f4")
        n = np.linalg.norm(d)
        if n > 1e-6:
            d /= n
        self.line(o, o + d * length, color)

    def _push(self, pos, color) -> None:
        if self._count >= self.MAX_VERTS:
            return
        self._buf[self._count, :3] = pos
        self._buf[self._count, 3:] = color
        self._count += 1
