"""
raycast.py
Mouse-click → world ray → entity selection.
Syncs selection to hierarchy panel + inspector panel.
"""
from __future__ import annotations
from typing import Optional, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from core.scene  import Scene
    from core.entity import Entity


def _normalize(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    return v if n < 1e-8 else v / n


# ------------------------------------------------------------------
# Ray
# ------------------------------------------------------------------

class Ray:
    def __init__(self, origin: np.ndarray, direction: np.ndarray):
        self.origin    = np.array(origin,    dtype="f4")
        self.direction = _normalize(np.array(direction, dtype="f4"))

    def at(self, t: float) -> np.ndarray:
        return self.origin + self.direction * t


def ray_from_screen(
    mouse_x: int, mouse_y: int,
    viewport_w: int, viewport_h: int,
    view: np.ndarray, proj: np.ndarray,
) -> Ray:
    ndc_x =  (2.0 * mouse_x / viewport_w) - 1.0
    ndc_y = -(2.0 * mouse_y / viewport_h) + 1.0

    inv_proj  = np.linalg.inv(proj)
    clip      = np.array([ndc_x, ndc_y, -1.0, 1.0], dtype="f4")
    eye       = inv_proj @ clip
    eye       = np.array([eye[0], eye[1], -1.0, 0.0], dtype="f4")

    inv_view  = np.linalg.inv(view)
    world_dir = inv_view @ eye
    origin    = inv_view[:, 3][:3]

    return Ray(origin, world_dir[:3])


# ------------------------------------------------------------------
# AABB helpers
# ------------------------------------------------------------------

def _entity_aabb(entity: "Entity"):
    """Return (world_min, world_max) for any renderable entity."""
    from core.mesh_renderer   import MeshRenderer
    from core.sprite_renderer import SpriteRenderer, Shape2DRenderer
    import core.primitives    as prim3d
    import core.primitives_2d as prim2d

    mr = entity.get_component(MeshRenderer)
    if mr is not None:
        try:
            verts = (mr._raw_vertices if mr.primitive == "custom" and
                     mr._raw_vertices is not None
                     else prim3d.generate(mr.primitive))
            positions = verts.reshape(-1, 8)[:, :3]
        except Exception:
            positions = prim3d.cube().reshape(-1, 8)[:, :3]
        model  = entity.transform.matrix
        ones   = np.ones((len(positions), 1), dtype="f4")
        world  = (model @ np.hstack([positions, ones]).T).T[:, :3]
        return world.min(axis=0), world.max(axis=0)

    sr = entity.get_component(SpriteRenderer) or \
         entity.get_component(Shape2DRenderer)
    if sr is not None:
        try:
            shape = getattr(sr, "shape", "square")
            verts = prim2d.generate_2d(shape).reshape(-1, 4)[:, :2]
        except Exception:
            verts = prim2d.square().reshape(-1, 4)[:, :2]
        size  = getattr(sr, "size", np.array([1, 1], dtype="f4"))
        verts = verts * size
        pos3  = np.hstack([verts,
                           np.zeros((len(verts), 1), dtype="f4")])
        model  = entity.transform.matrix
        ones   = np.ones((len(pos3), 1), dtype="f4")
        world  = (model @ np.hstack([pos3, ones]).T).T[:, :3]
        return world.min(axis=0), world.max(axis=0)

    # fallback: tiny box at transform position
    p = entity.transform.position
    return p - 0.3, p + 0.3


def ray_aabb(ray: Ray,
             aabb_min: np.ndarray,
             aabb_max: np.ndarray) -> Optional[float]:
    t_min, t_max = -np.inf, np.inf
    for i in range(3):
        d = ray.direction[i]
        if abs(d) < 1e-8:
            if ray.origin[i] < aabb_min[i] or ray.origin[i] > aabb_max[i]:
                return None
        else:
            t1 = (aabb_min[i] - ray.origin[i]) / d
            t2 = (aabb_max[i] - ray.origin[i]) / d
            t_min = max(t_min, min(t1, t2))
            t_max = min(t_max, max(t1, t2))
    if t_max < 0 or t_min > t_max:
        return None
    return t_min if t_min >= 0 else t_max


# ------------------------------------------------------------------
# Selector
# ------------------------------------------------------------------

class EntitySelector:
    def __init__(self, app):
        self.app = app
        self.selected_entity: Optional["Entity"] = None

    # ------------------------------------------------------------------

    def pick(self, mouse_x, mouse_y, viewport_w, viewport_h,
             view, proj, scene: "Scene") -> Optional["Entity"]:
        ray     = ray_from_screen(mouse_x, mouse_y,
                                  viewport_w, viewport_h, view, proj)
        best_t  = np.inf
        best    = None

        for entity in scene.entities:
            if not entity.enabled:
                continue
            try:
                mn, mx = _entity_aabb(entity)
            except Exception:
                continue
            t = ray_aabb(ray, mn, mx)
            if t is not None and t < best_t:
                best_t = t
                best   = entity

        self.selected_entity = best
        self.sync_to_ui()
        return best

    def select(self, entity: Optional["Entity"]) -> None:
        self.selected_entity = entity
        self.sync_to_ui()

    def clear(self) -> None:
        self.selected_entity = None
        self.sync_to_ui()

    # ------------------------------------------------------------------

    def sync_to_ui(self) -> None:
        """Push selection into inspector + hierarchy — uses correct attr names."""
        mw = getattr(self.app, "main_window", None)
        if mw is None:
            return
        e = self.selected_entity

        # --- inspector (attr is 'inspector' on MainWindow) ---
        inspector = getattr(mw, "inspector", None)
        if inspector is not None:
            if e:
                inspector.show_entity(e)
            else:
                inspector.clear()

        # --- hierarchy (attr is 'hierarchy' on MainWindow) ---
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
            scene_root = root.child(i)
            for j in range(scene_root.childCount()):
                child = scene_root.child(j)
                if child.data(0, Qt.UserRole) == e.id:
                    child.setSelected(True)
                    tree.scrollToItem(child)
                    return

    # ------------------------------------------------------------------

    def get_selection_aabb(self):
        if self.selected_entity is None:
            return None
        try:
            mn, mx = _entity_aabb(self.selected_entity)
            return (mn + mx) / 2, (mx - mn) / 2
        except Exception:
            return None