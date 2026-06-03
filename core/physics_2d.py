"""
physics_2d.py
Lightweight 2D physics — no heavy library needed.
Supports AABB and Circle colliders, velocity, gravity, overlap detection.
Runs entirely in Python/numpy; plugs into the scene update loop.
"""

from __future__ import annotations

import numpy as np
from typing import List, Optional, Tuple, TYPE_CHECKING

from core.component import Component

if TYPE_CHECKING:
    from core.entity import Entity
    from core.scene import Scene


# ------------------------------------------------------------------
# Collider components
# ------------------------------------------------------------------


class BoxCollider2D(Component):
    """Axis-aligned bounding box collider in 2D (XY plane)."""

    def __init__(
        self,
        width: float = 1.0,
        height: float = 1.0,
        offset: Tuple[float, float] = (0.0, 0.0),
    ):
        super().__init__()
        self.width = width
        self.height = height
        self.offset = np.array(offset, dtype="f4")
        self.is_trigger = False  # trigger = detect but don't resolve

    def world_rect(self) -> Tuple[np.ndarray, np.ndarray]:
        """Returns (min_xy, max_xy) in world space."""
        if self.entity is None:
            return np.zeros(2, dtype="f4"), np.zeros(2, dtype="f4")
        pos = self.entity.transform.position[:2] + self.offset
        half = np.array([self.width / 2, self.height / 2], dtype="f4")
        return pos - half, pos + half

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update(
            {
                "width": self.width,
                "height": self.height,
                "offset": self.offset.tolist(),
                "is_trigger": self.is_trigger,
            }
        )
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "BoxCollider2D":
        c = cls(data.get("width", 1), data.get("height", 1), data.get("offset", [0, 0]))
        c.is_trigger = data.get("is_trigger", False)
        c.enabled = data.get("enabled", True)
        return c


class CircleCollider2D(Component):
    """Circle collider in 2D."""

    def __init__(self, radius: float = 0.5, offset: Tuple[float, float] = (0.0, 0.0)):
        super().__init__()
        self.radius = radius
        self.offset = np.array(offset, dtype="f4")
        self.is_trigger = False

    def world_center(self) -> np.ndarray:
        if self.entity is None:
            return np.zeros(2, dtype="f4")
        return self.entity.transform.position[:2] + self.offset

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update(
            {
                "radius": self.radius,
                "offset": self.offset.tolist(),
                "is_trigger": self.is_trigger,
            }
        )
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "CircleCollider2D":
        c = cls(data.get("radius", 0.5), data.get("offset", [0, 0]))
        c.is_trigger = data.get("is_trigger", False)
        c.enabled = data.get("enabled", True)
        return c


# ------------------------------------------------------------------
# Rigidbody
# ------------------------------------------------------------------


class Rigidbody2D(Component):
    """Simple 2D rigidbody — velocity, gravity, drag."""

    def __init__(self):
        super().__init__()
        self.velocity: np.ndarray = np.zeros(2, dtype="f4")
        self.gravity_scale: float = 1.0
        self.drag: float = 0.02
        self.is_kinematic: bool = False  # kinematic = no physics, script-driven
        self.mass: float = 1.0
        self._grounded: bool = False

    def apply_force(self, fx: float, fy: float) -> None:
        if not self.is_kinematic:
            self.velocity += np.array([fx, fy], dtype="f4") / self.mass

    def apply_impulse(self, fx: float, fy: float) -> None:
        if not self.is_kinematic:
            self.velocity += np.array([fx, fy], dtype="f4")

    @property
    def grounded(self) -> bool:
        return self._grounded

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update(
            {
                "velocity": self.velocity.tolist(),
                "gravity_scale": self.gravity_scale,
                "drag": self.drag,
                "is_kinematic": self.is_kinematic,
                "mass": self.mass,
            }
        )
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Rigidbody2D":
        rb = cls()
        rb.velocity = np.array(data.get("velocity", [0, 0]), dtype="f4")
        rb.gravity_scale = data.get("gravity_scale", 1.0)
        rb.drag = data.get("drag", 0.02)
        rb.is_kinematic = data.get("is_kinematic", False)
        rb.mass = data.get("mass", 1.0)
        rb.enabled = data.get("enabled", True)
        return rb


# ------------------------------------------------------------------
# Collision result
# ------------------------------------------------------------------


class Collision2D:
    def __init__(
        self,
        entity_a: "Entity",
        entity_b: "Entity",
        normal: np.ndarray,
        penetration: float,
    ):
        self.entity_a = entity_a
        self.entity_b = entity_b
        self.normal = normal
        self.penetration = penetration


# ------------------------------------------------------------------
# Physics world
# ------------------------------------------------------------------

GRAVITY = np.array([0.0, -9.81], dtype="f4")


class PhysicsWorld2D:
    """
    Integrate into the scene update loop:
        physics_world.step(scene, delta_time)
    """

    def __init__(self, gravity_y: float = -9.81):
        self.gravity = np.array([0.0, gravity_y], dtype="f4")

    def step(self, scene: "Scene", dt: float) -> List[Collision2D]:
        entities = [e for e in scene.entities if e.enabled]
        collisions: List[Collision2D] = []

        # integrate velocity
        for e in entities:
            rb = e.get_component(Rigidbody2D)
            if rb is None or not rb.enabled or rb.is_kinematic:
                continue
            rb.velocity += self.gravity * rb.gravity_scale * dt
            rb.velocity *= 1.0 - rb.drag
            pos = e.transform.position
            pos[0] += rb.velocity[0] * dt
            pos[1] += rb.velocity[1] * dt
            e.transform._dirty = True

        # detect + resolve collisions
        for i, ea in enumerate(entities):
            for eb in entities[i + 1 :]:
                col = self._check(ea, eb)
                if col:
                    collisions.append(col)
                    if not col.entity_a.get_component(
                        Rigidbody2D
                    ) or not col.entity_b.get_component(Rigidbody2D):
                        continue
                    self._resolve(col)

        return collisions

    # ------------------------------------------------------------------

    def _check(self, ea: "Entity", eb: "Entity") -> Optional[Collision2D]:
        # box vs box
        ba = ea.get_component(BoxCollider2D)
        bb = eb.get_component(BoxCollider2D)
        if ba and bb and ba.enabled and bb.enabled:
            return self._box_box(ea, ba, eb, bb)

        # circle vs circle
        ca = ea.get_component(CircleCollider2D)
        cb = eb.get_component(CircleCollider2D)
        if ca and cb and ca.enabled and cb.enabled:
            return self._circle_circle(ea, ca, eb, cb)

        # box vs circle
        if ba and cb and ba.enabled and cb.enabled:
            return self._box_circle(ea, ba, eb, cb)
        if ca and bb and ca.enabled and bb.enabled:
            col = self._box_circle(eb, bb, ea, ca)
            if col:
                col.normal = -col.normal
                col.entity_a, col.entity_b = col.entity_b, col.entity_a
            return col

        return None

    def _box_box(self, ea, ba, eb, bb) -> Optional[Collision2D]:
        mn_a, mx_a = ba.world_rect()
        mn_b, mx_b = bb.world_rect()
        ox = min(mx_a[0], mx_b[0]) - max(mn_a[0], mn_b[0])
        oy = min(mx_a[1], mx_b[1]) - max(mn_a[1], mn_b[1])
        if ox <= 0 or oy <= 0:
            return None
        if ox < oy:
            normal = np.array([1, 0] if (mn_a[0] < mn_b[0]) else [-1, 0], dtype="f4")
            pen = ox
        else:
            normal = np.array([0, 1] if (mn_a[1] < mn_b[1]) else [0, -1], dtype="f4")
            pen = oy
        return Collision2D(ea, eb, normal, pen)

    def _circle_circle(self, ea, ca, eb, cb) -> Optional[Collision2D]:
        delta = cb.world_center() - ca.world_center()
        dist = np.linalg.norm(delta)
        radii = ca.radius + cb.radius
        if dist >= radii:
            return None
        normal = delta / dist if dist > 1e-8 else np.array([1, 0], dtype="f4")
        return Collision2D(ea, eb, normal, radii - dist)

    def _box_circle(self, ea, ba, eb, cb) -> Optional[Collision2D]:
        mn, mx = ba.world_rect()
        center = cb.world_center()
        closest = np.clip(center, mn, mx)
        delta = center - closest
        dist = np.linalg.norm(delta)
        if dist >= cb.radius:
            return None
        normal = delta / dist if dist > 1e-8 else np.array([0, 1], dtype="f4")
        return Collision2D(ea, eb, normal, cb.radius - dist)

    def _resolve(self, col: Collision2D) -> None:
        rb_a = col.entity_a.get_component(Rigidbody2D)
        rb_b = col.entity_b.get_component(Rigidbody2D)
        if rb_a is None or rb_b is None:
            return

        # positional correction
        correction = col.normal * col.penetration * 0.5
        if not rb_a.is_kinematic:
            col.entity_a.transform.position[:2] -= correction
            col.entity_a.transform._dirty = True
        if not rb_b.is_kinematic:
            col.entity_b.transform.position[:2] += correction
            col.entity_b.transform._dirty = True

        # velocity reflection
        rel_vel = rb_b.velocity - rb_a.velocity
        vel_along = np.dot(rel_vel, col.normal)
        if vel_along > 0:
            return
        restitution = 0.3
        impulse = -(1 + restitution) * vel_along / (1 / rb_a.mass + 1 / rb_b.mass)
        imp_vec = impulse * col.normal
        if not rb_a.is_kinematic:
            rb_a.velocity -= imp_vec / rb_a.mass
        if not rb_b.is_kinematic:
            rb_b.velocity += imp_vec / rb_b.mass
