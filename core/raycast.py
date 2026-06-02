"""
raycast.py
Mouse-click → world ray → entity selection.
Supports AABB intersection for MeshRenderer and SpriteRenderer.
Syncs selection to the scene hierarchy and inspector panels.
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from core.scene import Scene
    from core.entity import Entity


def _normalize(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    return v if n < 1e-8 else v / n


# ------------------------------------------------------------------
# Ray
# ------------------------------------------------------------------


class Ray:
    def __init__(self, origin: np.ndarray, direction: np.ndarray):
        self.origin = np.array(origin, dtype="f4")
        self.direction = _normalize(np.array(direction, dtype="f4"))

    def at(self, t: float) -> np.ndarray:
        return self.origin + self.direction * t


def ray_from_screen(
    mouse_x: int,
    mouse_y: int,
    viewport_w: int,
    viewport_h: int,
    view: np.ndarray,
    proj: np.ndarray,
) -> Ray:
    """Unproject mouse position into a world-space ray."""
    # NDC
    ndc_x = (2.0 * mouse_x / viewport_w) - 1.0
    ndc_y = -(2.0 * mouse_y / viewport_h) + 1.0

    # clip → eye
    inv_proj = np.linalg.inv(proj)
    clip = np.array([ndc_x, ndc_y, -1.0, 1.0], dtype="f4")
    eye = inv_proj @ clip
    eye = np.array([eye[0], eye[1], -1.0, 0.0], dtype="f4")

    # eye → world
    inv_view = np.linalg.inv(view)
    world_dir = inv_view @ eye
    origin = inv_view[:, 3][:3]

    return Ray(origin, world_dir[:3])


# ------------------------------------------------------------------
# AABB helpers
# ------------------------------------------------------------------


def _mesh_aabb(entity: "Entity") -> tuple[np.ndarray, np.ndarray]:
    """Return (world_min, world_max) AABB for a MeshRenderer entity."""
    from core.mesh_renderer import MeshRenderer
    import core.primitives as prim

    mr = entity.get_component(MeshRenderer)
    if mr is None:
        return np.zeros(3, dtype="f4"), np.zeros(3, dtype="f4")

    try:
        verts = prim.generate(mr.primitive)
    except Exception:
        verts = prim.cube()

    # positions are every 8th stride starting at 0
    positions = verts.reshape(-1, 8)[:, :3]

    model = entity.transform.matrix
    ones = np.ones((len(positions), 1), dtype="f4")
    world = (model @ np.hstack([positions, ones]).T).T[:, :3]

    return world.min(axis=0), world.max(axis=0)


def ray_aabb(ray: Ray, aabb_min: np.ndarray, aabb_max: np.ndarray) -> Optional[float]:
    """Slab method. Returns t of intersection or None."""
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
    """
    Manages the currently selected entity.
    Call pick() on mouse press, then sync_to_ui() to update panels.
    """

    def __init__(self, app):
        self.app = app
        self.selected_entity: Optional["Entity"] = None

    def pick(
        self,
        mouse_x: int,
        mouse_y: int,
        viewport_w: int,
        viewport_h: int,
        view: np.ndarray,
        proj: np.ndarray,
        scene: "Scene",
    ) -> Optional["Entity"]:
        ray = ray_from_screen(mouse_x, mouse_y, viewport_w, viewport_h, view, proj)
        best_t: float = np.inf
        best_entity: Optional["Entity"] = None

        for entity in scene.entities:
            if not entity.enabled:
                continue
            try:
                aabb_min, aabb_max = _mesh_aabb(entity)
            except Exception:
                continue

            t = ray_aabb(ray, aabb_min, aabb_max)
            if t is not None and t < best_t:
                best_t = t
                best_entity = entity

        self.selected_entity = best_entity
        self.sync_to_ui()
        return best_entity

    def select(self, entity: Optional["Entity"]) -> None:
        self.selected_entity = entity
        self.sync_to_ui()

    def clear(self) -> None:
        self.selected_entity = None
        self.sync_to_ui()

    def sync_to_ui(self) -> None:
        """Push selection into scene hierarchy + inspector."""
        mw = self.app.main_window
        e = self.selected_entity

        # inspector
        if hasattr(mw, "inspector_panel"):
            if e:
                mw.inspector_panel.show_entity(e)
            else:
                mw.inspector_panel.clear()

        # hierarchy — highlight matching item
        if hasattr(mw, "scene_hierarchy"):
            tree = mw.scene_hierarchy
            tree.clearSelection()
            if e is None:
                return
            it = tree.invisibleRootItem()
            for i in range(it.childCount()):
                root_item = it.child(i)
                for j in range(root_item.childCount()):
                    child = root_item.child(j)
                    from PySide6.QtCore import Qt

                    if child.data(0, Qt.UserRole) == e.id:
                        child.setSelected(True)
                        tree.scrollToItem(child)
                        return

    def get_selection_aabb(self):
        """Returns (center, half_extents) for the selected entity, or None."""
        if self.selected_entity is None:
            return None
        try:
            mn, mx = _mesh_aabb(self.selected_entity)
            center = (mn + mx) / 2
            half = (mx - mn) / 2
            return center, half
        except Exception:
            return None
