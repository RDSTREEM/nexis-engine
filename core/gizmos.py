from __future__ import annotations
import math
from typing import Optional, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from core.entity import Entity
    from core.debug_draw import DebugDraw


# ------------------------------------------------------------------
# Colours
# ------------------------------------------------------------------
_X = (1.0, 0.2, 0.2)
_Y = (0.2, 1.0, 0.2)
_Z = (0.2, 0.4, 1.0)
_XY = (1.0, 1.0, 0.2)
_HL = (1.0, 1.0, 1.0)  # highlight

# Gizmo modes
TRANSLATE = "translate"
ROTATE = "rotate"
SCALE = "scale"

# Axes
AXIS_X = 0
AXIS_Y = 1
AXIS_Z = 2
AXIS_XY = 3  # 2D combined


def _project_to_screen(
    world_pos: np.ndarray, view: np.ndarray, proj: np.ndarray, vw: int, vh: int
) -> Optional[np.ndarray]:
    p = np.array([*world_pos, 1.0], dtype="f4")
    clip = proj @ view @ p
    if abs(clip[3]) < 1e-8:
        return None
    ndc = clip[:3] / clip[3]
    sx = (ndc[0] + 1) * 0.5 * vw
    sy = (1 - ndc[1]) * 0.5 * vh
    return np.array([sx, sy], dtype="f4")


def _screen_dist(a: np.ndarray, b: np.ndarray) -> float:
    d = a - b
    return float(np.sqrt(d[0] * d[0] + d[1] * d[1]))


class Gizmo:
    """
    Single gizmo that works in both 2D and 3D mode.
    In 2D mode only X/Y handles are shown and Z is hidden.
    """

    HANDLE_SIZE = 1.2  # world-space length of axis arms
    HIT_RADIUS_PX = 12  # pixels — how close mouse must be to grab

    def __init__(self):
        self.mode: str = TRANSLATE
        self._entity: Optional["Entity"] = None
        self._active_axis: Optional[int] = None
        self._drag_start_world: Optional[np.ndarray] = None
        self._drag_start_pos: Optional[np.ndarray] = None
        self._drag_start_scale: Optional[np.ndarray] = None
        self._drag_start_angle: float = 0.0
        self._is_2d: bool = False

    # ------------------------------------------------------------------

    def set_entity(self, entity: Optional["Entity"]) -> None:
        self._entity = entity

    def set_mode(self, mode: str) -> None:
        self.mode = mode

    def set_2d(self, is_2d: bool) -> None:
        self._is_2d = is_2d

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(
        self, dd: "DebugDraw", view: np.ndarray, proj: np.ndarray, vw: int, vh: int
    ) -> None:
        if self._entity is None:
            return
        origin = self._entity.transform.position.copy()
        s = self.HANDLE_SIZE

        if self.mode == TRANSLATE:
            self._draw_translate(dd, origin, s)
        elif self.mode == SCALE:
            self._draw_scale(dd, origin, s)
        elif self.mode == ROTATE and not self._is_2d:
            self._draw_rotate_3d(dd, origin, s)
        elif self.mode == ROTATE and self._is_2d:
            self._draw_rotate_2d(dd, origin, s)

    def _draw_translate(self, dd, o, s):
        ax = AXIS_X == self._active_axis
        ay = AXIS_Y == self._active_axis
        az = AXIS_Z == self._active_axis
        # X arrow
        dd.line(o, o + np.array([s, 0, 0]), _HL if ax else _X)
        dd.line(
            o + np.array([s, 0, 0]), o + np.array([s - 0.2, 0.1, 0]), _HL if ax else _X
        )
        dd.line(
            o + np.array([s, 0, 0]), o + np.array([s - 0.2, -0.1, 0]), _HL if ax else _X
        )
        # Y arrow
        dd.line(o, o + np.array([0, s, 0]), _HL if ay else _Y)
        dd.line(
            o + np.array([0, s, 0]), o + np.array([0.1, s - 0.2, 0]), _HL if ay else _Y
        )
        dd.line(
            o + np.array([0, s, 0]), o + np.array([-0.1, s - 0.2, 0]), _HL if ay else _Y
        )
        # Z arrow (3D only)
        if not self._is_2d:
            dd.line(o, o + np.array([0, 0, s]), _HL if az else _Z)
            dd.line(
                o + np.array([0, 0, s]),
                o + np.array([0.1, 0, s - 0.2]),
                _HL if az else _Z,
            )
            dd.line(
                o + np.array([0, 0, s]),
                o + np.array([0, 0.1, s - 0.2]),
                _HL if az else _Z,
            )
        # XY plane square (2D)
        if self._is_2d:
            q = s * 0.3
            pts = [
                o + np.array([0, 0, 0]),
                o + np.array([q, 0, 0]),
                o + np.array([q, q, 0]),
                o + np.array([0, q, 0]),
            ]
            c = _HL if self._active_axis == AXIS_XY else _XY
            for i in range(4):
                dd.line(pts[i], pts[(i + 1) % 4], c)

    def _draw_scale(self, dd, o, s):
        ax = AXIS_X == self._active_axis
        ay = AXIS_Y == self._active_axis
        az = AXIS_Z == self._active_axis
        # X
        dd.line(o, o + np.array([s, 0, 0]), _HL if ax else _X)
        ep = o + np.array([s, 0, 0])
        dd.wire_box(ep, (0.07, 0.07, 0.07), _HL if ax else _X)
        # Y
        dd.line(o, o + np.array([0, s, 0]), _HL if ay else _Y)
        ep = o + np.array([0, s, 0])
        dd.wire_box(ep, (0.07, 0.07, 0.07), _HL if ay else _Y)
        # Z (3D only)
        if not self._is_2d:
            dd.line(o, o + np.array([0, 0, s]), _HL if az else _Z)
            ep = o + np.array([0, 0, s])
            dd.wire_box(ep, (0.07, 0.07, 0.07), _HL if az else _Z)

    def _draw_rotate_3d(self, dd, o, s):
        segs = 32
        for axis, col in ((0, _X), (1, _Y), (2, _Z)):
            prev = None
            for i in range(segs + 1):
                a = 2 * math.pi * i / segs
                if axis == 0:
                    pt = o + np.array([0, math.cos(a) * s, math.sin(a) * s])
                elif axis == 1:
                    pt = o + np.array([math.cos(a) * s, 0, math.sin(a) * s])
                else:
                    pt = o + np.array([math.cos(a) * s, math.sin(a) * s, 0])
                if prev is not None:
                    dd.line(prev, pt, _HL if self._active_axis == axis else col)
                prev = pt

    def _draw_rotate_2d(self, dd, o, s):
        dd.wire_sphere(o, s, _HL if self._active_axis == AXIS_Z else _Z, segments=32)

    # ------------------------------------------------------------------
    # Mouse interaction
    # ------------------------------------------------------------------

    def on_mouse_press(self, mx, my, view, proj, vw, vh) -> bool:
        """Returns True if the gizmo consumed the click."""
        if self._entity is None:
            return False
        axis = self._hit_test(mx, my, view, proj, vw, vh)
        if axis is None:
            return False
        self._active_axis = axis
        self._drag_start_world = self._unproject(mx, my, view, proj, vw, vh)
        self._drag_start_pos = self._entity.transform.position.copy()
        self._drag_start_scale = self._entity.transform.scale.copy()
        # for rotate: store initial angle
        o = self._entity.transform.position
        self._drag_start_angle = math.atan2(
            self._drag_start_world[1] - o[1], self._drag_start_world[0] - o[0]
        )
        return True

    def on_mouse_move(self, mx, my, view, proj, vw, vh) -> bool:
        if self._active_axis is None or self._entity is None:
            return False
        world = self._unproject(mx, my, view, proj, vw, vh)
        delta = world - self._drag_start_world

        t = self._entity.transform
        if self.mode == TRANSLATE:
            new_pos = self._drag_start_pos.copy()
            if self._active_axis == AXIS_X:
                new_pos[0] += delta[0]
            elif self._active_axis == AXIS_Y:
                new_pos[1] += delta[1]
            elif self._active_axis == AXIS_Z:
                new_pos[2] += delta[2]
            elif self._active_axis == AXIS_XY:
                new_pos[0] += delta[0]
                new_pos[1] += delta[1]
            t.position[:] = new_pos

        elif self.mode == SCALE:
            mag = float(np.linalg.norm(delta))
            sign = (
                1.0
                if (delta[self._active_axis] >= 0 if self._active_axis < 3 else True)
                else -1.0
            )
            s_new = self._drag_start_scale.copy()
            idx = min(self._active_axis, 2)
            s_new[idx] = max(0.01, self._drag_start_scale[idx] + sign * mag)
            t.scale[:] = s_new

        elif self.mode == ROTATE:
            o = t.position
            angle = math.atan2(world[1] - o[1], world[0] - o[0])
            diff = math.degrees(angle - self._drag_start_angle)
            if self._active_axis == AXIS_Z or self._is_2d:
                t.rotation[2] += diff
            elif self._active_axis == AXIS_X:
                t.rotation[0] += diff
            elif self._active_axis == AXIS_Y:
                t.rotation[1] += diff
            self._drag_start_angle = angle

        t._dirty = True
        # refresh inspector live
        mw = getattr(self._entity.scene, "_app", None)
        return True

    def on_mouse_release(self) -> None:
        self._active_axis = None
        self._drag_start_world = None
        self._drag_start_pos = None
        self._drag_start_scale = None

    def is_dragging(self) -> bool:
        return self._active_axis is not None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _hit_test(self, mx, my, view, proj, vw, vh) -> Optional[int]:
        if self._entity is None:
            return None
        o = self._entity.transform.position
        s = self.HANDLE_SIZE
        mpt = np.array([mx, my], dtype="f4")

        candidates = {
            AXIS_X: o + np.array([s, 0, 0]),
            AXIS_Y: o + np.array([0, s, 0]),
        }
        if not self._is_2d:
            candidates[AXIS_Z] = o + np.array([0, 0, s])
        if self._is_2d:
            candidates[AXIS_XY] = o + np.array([s * 0.3, s * 0.3, 0])

        best_dist = self.HIT_RADIUS_PX
        best_axis = None
        for axis, tip in candidates.items():
            sp = _project_to_screen(tip, view, proj, vw, vh)
            if sp is None:
                continue
            d = _screen_dist(mpt, sp)
            if d < best_dist:
                best_dist = d
                best_axis = axis
        return best_axis

    def _unproject(self, mx, my, view, proj, vw, vh) -> np.ndarray:
        """Screen → world point on the entity's Z plane."""
        from core.raycast import ray_from_screen_3d, world_pos_from_screen_2d

        if self._is_2d:
            return world_pos_from_screen_2d(mx, my, vw, vh, view, proj)
        ray = ray_from_screen_3d(mx, my, vw, vh, view, proj)
        # intersect with Z=entity.z plane
        ez = self._entity.transform.position[2] if self._entity else 0
        dz = ray.direction[2]
        if abs(dz) < 1e-8:
            return ray.origin
        t = (ez - ray.origin[2]) / dz
        return ray.at(t)
