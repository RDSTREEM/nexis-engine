"""
raycast.py
Unified raycasting for both 3D (perspective) and 2D (orthographic) modes.
2D mode unprojects mouse to XY world plane directly — no ray/AABB needed.
"""
from __future__ import annotations
from typing import Optional, Tuple, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from core.scene  import Scene
    from core.entity import Entity


def _normalize(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    return v if n < 1e-8 else v / n


# ------------------------------------------------------------------
# Ray (3D)
# ------------------------------------------------------------------

class Ray:
    def __init__(self, origin: np.ndarray, direction: np.ndarray):
        self.origin    = np.array(origin,    dtype="f4")
        self.direction = _normalize(np.array(direction, dtype="f4"))

    def at(self, t: float) -> np.ndarray:
        return self.origin + self.direction * t


def ray_from_screen_3d(mx, my, vw, vh,
                        view: np.ndarray,
                        proj: np.ndarray) -> Ray:
    ndc_x =  (2.0 * mx / vw) - 1.0
    ndc_y = -(2.0 * my / vh) + 1.0
    inv_proj  = np.linalg.inv(proj)
    clip      = np.array([ndc_x, ndc_y, -1.0, 1.0], dtype="f4")
    eye       = inv_proj @ clip
    eye       = np.array([eye[0], eye[1], -1.0, 0.0], dtype="f4")
    inv_view  = np.linalg.inv(view)
    world_dir = inv_view @ eye
    origin    = inv_view[:, 3][:3]
    return Ray(origin, world_dir[:3])


def world_pos_from_screen_2d(mx, my, vw, vh,
                              view: np.ndarray,
                              proj: np.ndarray) -> np.ndarray:
    """
    Orthographic unproject — returns XY world position for a mouse click.
    Used in 2D mode instead of ray casting.
    """
    ndc_x =  (2.0 * mx / vw) - 1.0
    ndc_y = -(2.0 * my / vh) + 1.0
    clip      = np.array([ndc_x, ndc_y, 0.0, 1.0], dtype="f4")
    inv_vp    = np.linalg.inv(proj @ view)
    world     = inv_vp @ clip
    if abs(world[3]) > 1e-8:
        world /= world[3]
    return world[:3].astype("f4")


# ------------------------------------------------------------------
# AABB helpers
# ------------------------------------------------------------------

def _entity_aabb_3d(entity: "Entity"):
    """Returns (world_min, world_max) for 3D entities."""
    from core.mesh_renderer import MeshRenderer
    import core.primitives  as prim3d

    mr = entity.get_component(MeshRenderer)
    if mr is None:
        p = entity.transform.position
        return p - 0.3, p + 0.3

    try:
        verts = (mr._raw_vertices
                 if mr.primitive == "custom" and mr._raw_vertices is not None
                 else prim3d.generate(mr.primitive))
        positions = verts.reshape(-1, 8)[:, :3]
    except Exception:
        positions = prim3d.cube().reshape(-1, 8)[:, :3]

    model = entity.transform.matrix
    ones  = np.ones((len(positions), 1), dtype="f4")
    world = (model @ np.hstack([positions, ones]).T).T[:, :3]
    return world.min(axis=0), world.max(axis=0)


def _entity_aabb_2d(entity: "Entity") -> Tuple[np.ndarray, np.ndarray]:
    """Returns (world_min_xy, world_max_xy) for 2D entities on the XY plane."""
    from core.sprite_renderer import SpriteRenderer, Shape2DRenderer
    import core.primitives_2d as prim2d

    sr = (entity.get_component(SpriteRenderer) or
          entity.get_component(Shape2DRenderer))

    if sr is not None:
        try:
            shape = getattr(sr, "shape", "square")
            verts = prim2d.generate_2d(shape).reshape(-1, 4)[:, :2]
        except Exception:
            verts = prim2d.square().reshape(-1, 4)[:, :2]
        size  = getattr(sr, "size", np.array([1.0, 1.0], dtype="f4"))
        verts = verts * size
    else:
        # fallback — half-unit box
        verts = np.array([[-0.5,-0.5],[0.5,-0.5],
                          [0.5,0.5],[-0.5,0.5]], dtype="f4")

    pos3  = np.hstack([verts, np.zeros((len(verts), 1), dtype="f4")])
    model = entity.transform.matrix
    ones  = np.ones((len(pos3), 1), dtype="f4")
    world = (model @ np.hstack([pos3, ones]).T).T[:, :3]
    return world[:, :2].min(axis=0), world[:, :2].max(axis=0)


def ray_aabb(ray: Ray, mn: np.ndarray, mx: np.ndarray) -> Optional[float]:
    t_min, t_max = -np.inf, np.inf
    for i in range(3):
        d = ray.direction[i]
        if abs(d) < 1e-8:
            if ray.origin[i] < mn[i] or ray.origin[i] > mx[i]:
                return None
        else:
            t1 = (mn[i] - ray.origin[i]) / d
            t2 = (mx[i] - ray.origin[i]) / d
            t_min = max(t_min, min(t1, t2))
            t_max = min(t_max, max(t1, t2))
    if t_max < 0 or t_min > t_max:
        return None
    return t_min if t_min >= 0 else t_max


def point_in_aabb_2d(point: np.ndarray,
                      mn: np.ndarray,
                      mx: np.ndarray) -> bool:
    return (mn[0] <= point[0] <= mx[0] and
            mn[1] <= point[1] <= mx[1])


# ------------------------------------------------------------------
# Selector
# ------------------------------------------------------------------

class EntitySelector:
    def __init__(self, app):
        self.app = app
        self.selected_entity: Optional["Entity"] = None

    # ------------------------------------------------------------------

    def pick(self, mx, my, vw, vh,
             view, proj, scene: "Scene",
             mode: str = "3d") -> Optional["Entity"]:
        """
        mode = "3d" → perspective ray-AABB
        mode = "2d" → orthographic point-in-AABB on XY plane
        """
        if mode == "2d":
            return self._pick_2d(mx, my, vw, vh, view, proj, scene)
        return self._pick_3d(mx, my, vw, vh, view, proj, scene)

    def _pick_3d(self, mx, my, vw, vh, view, proj, scene):
        ray    = ray_from_screen_3d(mx, my, vw, vh, view, proj)
        best_t = np.inf
        best   = None
        for entity in scene.entities:
            if not entity.enabled:
                continue
            try:
                mn, mx_ = _entity_aabb_3d(entity)
                # pad AABB slightly so thin objects are still pickable
                pad = np.array([0.05, 0.05, 0.05], dtype="f4")
                t   = ray_aabb(ray, mn - pad, mx_ + pad)
                if t is not None and t < best_t:
                    best_t = t
                    best   = entity
            except Exception:
                continue
        if best is None and self.selected_entity is not None:
            # clicked empty space — deselect cleanly
            self.selected_entity = None
            self.sync_to_ui()
        elif best is not None:
            self.selected_entity = best
            self.sync_to_ui()
        return best

    def _pick_2d(self, mx, my, vw, vh, view, proj, scene):
        world_pt = world_pos_from_screen_2d(mx, my, vw, vh, view, proj)
        best_area = np.inf
        best      = None
        for entity in scene.entities:
            if not entity.enabled:
                continue
            try:
                mn, mx_ = _entity_aabb_2d(entity)
                if point_in_aabb_2d(world_pt[:2], mn, mx_):
                    # pick smallest entity when overlapping
                    area = float((mx_[0]-mn[0]) * (mx_[1]-mn[1]))
                    if area < best_area:
                        best_area = area
                        best      = entity
            except Exception:
                continue
        if best is None and self.selected_entity is not None:
            self.selected_entity = None
            self.sync_to_ui()
        elif best is not None:
            self.selected_entity = best
            self.sync_to_ui()
        return best

    # ------------------------------------------------------------------

    def select(self, entity: Optional["Entity"]) -> None:
        self.selected_entity = entity
        self.sync_to_ui()

    def clear(self) -> None:
        self.selected_entity = None
        self.sync_to_ui()

    def sync_to_ui(self) -> None:
        mw = getattr(self.app, "main_window", None)
        if mw is None:
            return
        e = self.selected_entity

        inspector = getattr(mw, "inspector", None)
        if inspector:
            inspector.show_entity(e) if e else inspector.clear()

        hierarchy = getattr(mw, "hierarchy", None)
        if hierarchy is None:
            return
        tree = hierarchy.tree
        tree.clearSelection()
        if e is None:
            return
        from PySide6.QtCore import Qt
        root = tree.invisibleRootItem()
        for i in range(root.childCount()):
            r = root.child(i)
            for j in range(r.childCount()):
                child = r.child(j)
                if child.data(0, Qt.UserRole) == e.id:
                    child.setSelected(True)
                    tree.scrollToItem(child)
                    return

    def get_selection_aabb(self):
        e = self.selected_entity
        if e is None:
            return None
        try:
            cam_mode = self.app.main_window.viewport.camera.mode
            if cam_mode == "2d":
                mn, mx = _entity_aabb_2d(e)
                mn3 = np.array([mn[0], mn[1], -0.1], dtype="f4")
                mx3 = np.array([mx[0], mx[1],  0.1], dtype="f4")
            else:
                mn3, mx3 = _entity_aabb_3d(e)
            return (mn3 + mx3) / 2, (mx3 - mn3) / 2
        except Exception:
            return None