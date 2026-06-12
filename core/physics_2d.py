from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable

from core.component import Component

# ── Physics Body ─────────────────────────────────────────────────────────────


@dataclass
class PhysicsBody:
    entity_id: str
    position: List[float] = field(default_factory=lambda: [0.0, 0.0])
    velocity: List[float] = field(default_factory=lambda: [0.0, 0.0])
    mass: float = 1.0
    inv_mass: float = 1.0
    is_kinematic: bool = False
    gravity_scale: float = 1.0
    drag: float = 0.05
    # Shape: "box" | "circle" | None
    shape: Optional[str] = None
    shape_data: dict = field(default_factory=dict)  # {"w":, "h":} or {"r":}
    is_trigger: bool = False

    def __post_init__(self):
        if self.is_kinematic or self.mass <= 0:
            self.inv_mass = 0.0
        else:
            self.inv_mass = 1.0 / self.mass


# ── World ────────────────────────────────────────────────────────────────────


class PhysicsWorld2D:
    def __init__(self, gravity=(0.0, -9.81)):
        self.gravity: Tuple[float, float] = gravity
        self._bodies: Dict[str, PhysicsBody] = {}
        self._collision_events: List[Tuple[str, str, bool]] = []
        self._prev_pairs: set = set()

    # ── Body management ───────────────────────────────────────────────────────

    def add_body(
        self,
        entity_id: str,
        x: float = 0.0,
        y: float = 0.0,
        mass: float = 1.0,
        is_kinematic: bool = False,
        gravity_scale: float = 1.0,
        drag: float = 0.05,
    ) -> PhysicsBody:
        body = PhysicsBody(
            entity_id=entity_id,
            position=[x, y],
            mass=mass,
            is_kinematic=is_kinematic,
            gravity_scale=gravity_scale,
            drag=drag,
        )
        self._bodies[entity_id] = body
        return body

    def get_body(self, entity_id: str) -> Optional[PhysicsBody]:
        return self._bodies.get(entity_id)

    def remove_body(self, entity_id: str) -> None:
        self._bodies.pop(entity_id, None)

    def set_box_shape(
        self, entity_id: str, w: float, h: float, is_trigger: bool = False
    ) -> None:
        b = self._bodies.get(entity_id)
        if b:
            b.shape = "box"
            b.shape_data = {"w": w, "h": h}
            b.is_trigger = is_trigger

    def set_circle_shape(
        self, entity_id: str, radius: float, is_trigger: bool = False
    ) -> None:
        b = self._bodies.get(entity_id)
        if b:
            b.shape = "circle"
            b.shape_data = {"r": radius}
            b.is_trigger = is_trigger

    # ── Simulation step ───────────────────────────────────────────────────────

    def step(self, dt: float) -> None:
        gx, gy = self.gravity

        for body in self._bodies.values():
            if body.is_kinematic or body.inv_mass == 0:
                continue

            # Gravity
            body.velocity[0] += gx * body.gravity_scale * dt
            body.velocity[1] += gy * body.gravity_scale * dt

            # Drag
            drag = max(0.0, 1.0 - body.drag * dt)
            body.velocity[0] *= drag
            body.velocity[1] *= drag

            # Integrate
            body.position[0] += body.velocity[0] * dt
            body.position[1] += body.velocity[1] * dt

        # Collision detection + resolution
        self._detect_and_resolve()

    # ── AABB/Circle broad + narrow phase ─────────────────────────────────────

    def _detect_and_resolve(self) -> None:
        bodies = list(self._bodies.values())
        current_pairs: set = set()

        for i in range(len(bodies)):
            for j in range(i + 1, len(bodies)):
                a = bodies[i]
                b = bodies[j]
                if a.shape is None or b.shape is None:
                    continue

                overlap, normal = self._test_overlap(a, b)
                if overlap is None:
                    continue

                pair = (a.entity_id, b.entity_id)
                current_pairs.add(pair)

                # Fire enter/exit events
                if pair not in self._prev_pairs:
                    self._collision_events.append((a.entity_id, b.entity_id, True))

                # Resolve (skip triggers)
                if not a.is_trigger and not b.is_trigger:
                    self._resolve(a, b, overlap, normal)

        # Exit events for pairs that ended
        for pair in self._prev_pairs - current_pairs:
            self._collision_events.append((pair[0], pair[1], False))

        self._prev_pairs = current_pairs

    def _test_overlap(self, a: PhysicsBody, b: PhysicsBody):
        """Returns (overlap_depth, normal) or (None, None)."""
        if a.shape == "box" and b.shape == "box":
            return self._aabb_vs_aabb(a, b)
        if a.shape == "circle" and b.shape == "circle":
            return self._circle_vs_circle(a, b)
        if a.shape == "box" and b.shape == "circle":
            return self._aabb_vs_circle(a, b)
        if a.shape == "circle" and b.shape == "box":
            ov, n = self._aabb_vs_circle(b, a)
            if n is not None:
                return ov, (-n[0], -n[1])
            return None, None
        return None, None

    def _aabb_vs_aabb(self, a: PhysicsBody, b: PhysicsBody):
        hw_a = a.shape_data["w"] / 2
        hh_a = a.shape_data["h"] / 2
        hw_b = b.shape_data["w"] / 2
        hh_b = b.shape_data["h"] / 2

        dx = b.position[0] - a.position[0]
        dy = b.position[1] - a.position[1]
        ox = (hw_a + hw_b) - abs(dx)
        oy = (hh_a + hh_b) - abs(dy)

        if ox <= 0 or oy <= 0:
            return None, None
        if ox < oy:
            nx = 1.0 if dx > 0 else -1.0
            return ox, (nx, 0.0)
        else:
            ny = 1.0 if dy > 0 else -1.0
            return oy, (0.0, ny)

    def _circle_vs_circle(self, a: PhysicsBody, b: PhysicsBody):
        ra = a.shape_data["r"]
        rb = b.shape_data["r"]
        dx = b.position[0] - a.position[0]
        dy = b.position[1] - a.position[1]
        dist2 = dx * dx + dy * dy
        min_d = ra + rb
        if dist2 >= min_d * min_d:
            return None, None
        dist = math.sqrt(dist2) or 1e-8
        return (min_d - dist), (dx / dist, dy / dist)

    def _aabb_vs_circle(self, box: PhysicsBody, circle: PhysicsBody):
        hw = box.shape_data["w"] / 2
        hh = box.shape_data["h"] / 2
        r = circle.shape_data["r"]
        cx = circle.position[0] - box.position[0]
        cy = circle.position[1] - box.position[1]
        clamp_x = max(-hw, min(hw, cx))
        clamp_y = max(-hh, min(hh, cy))
        dx = cx - clamp_x
        dy = cy - clamp_y
        dist2 = dx * dx + dy * dy
        if dist2 >= r * r:
            return None, None
        dist = math.sqrt(dist2) or 1e-8
        return (r - dist), (dx / dist, dy / dist)

    def _resolve(
        self,
        a: PhysicsBody,
        b: PhysicsBody,
        overlap: float,
        normal: Tuple[float, float],
    ) -> None:
        nx, ny = normal
        total_inv = a.inv_mass + b.inv_mass
        if total_inv == 0:
            return

        # Positional correction (prevent sinking)
        correction = overlap / total_inv * 0.8
        a.position[0] -= nx * correction * a.inv_mass
        a.position[1] -= ny * correction * a.inv_mass
        b.position[0] += nx * correction * b.inv_mass
        b.position[1] += ny * correction * b.inv_mass

        # Impulse resolution
        rv_x = b.velocity[0] - a.velocity[0]
        rv_y = b.velocity[1] - a.velocity[1]
        vel_along_normal = rv_x * nx + rv_y * ny

        if vel_along_normal > 0:
            return  # separating

        restitution = 0.3
        j = -(1 + restitution) * vel_along_normal / total_inv

        a.velocity[0] -= j * nx * a.inv_mass
        a.velocity[1] -= j * ny * a.inv_mass
        b.velocity[0] += j * nx * b.inv_mass
        b.velocity[1] += j * ny * b.inv_mass


# ── Components ────────────────────────────────────────────────────────────────


class Rigidbody2D(Component):
    def __init__(self):
        super().__init__()
        self.mass: float = 1.0
        self.gravity_scale: float = 1.0
        self.drag: float = 0.05
        self.is_kinematic: bool = False
        self.velocity: list = [0.0, 0.0]  # synced from PhysicsBody

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update(
            {
                "mass": self.mass,
                "gravity_scale": self.gravity_scale,
                "drag": self.drag,
                "is_kinematic": self.is_kinematic,
            }
        )
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Rigidbody2D":
        rb = cls()
        rb.enabled = data.get("enabled", True)
        rb.mass = data.get("mass", 1.0)
        rb.gravity_scale = data.get("gravity_scale", 1.0)
        rb.drag = data.get("drag", 0.05)
        rb.is_kinematic = data.get("is_kinematic", False)
        return rb


class BoxCollider2D(Component):
    def __init__(self, width: float = 1.0, height: float = 1.0):
        super().__init__()
        self.width: float = width
        self.height: float = height
        self.is_trigger: bool = False
        self.on_collision_enter: Optional[Callable] = None
        self.on_collision_exit: Optional[Callable] = None

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update(
            {"width": self.width, "height": self.height, "is_trigger": self.is_trigger}
        )
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "BoxCollider2D":
        c = cls(data.get("width", 1.0), data.get("height", 1.0))
        c.enabled = data.get("enabled", True)
        c.is_trigger = data.get("is_trigger", False)
        return c


class CircleCollider2D(Component):
    def __init__(self, radius: float = 0.5):
        super().__init__()
        self.radius: float = radius
        self.is_trigger: bool = False
        self.on_collision_enter: Optional[Callable] = None
        self.on_collision_exit: Optional[Callable] = None

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({"radius": self.radius, "is_trigger": self.is_trigger})
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "CircleCollider2D":
        c = cls(data.get("radius", 0.5))
        c.enabled = data.get("enabled", True)
        c.is_trigger = data.get("is_trigger", False)
        return c
