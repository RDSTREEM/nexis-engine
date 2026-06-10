"""
play_mode.py
FIX: Physics world ticked every frame.
FIX: Body positions synced back to entity transforms.
FIX: Collision callbacks fired to scripts.
FIX: on_input forwarded to all scripts each frame.
"""

from __future__ import annotations
import copy
import time
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app import NexisApp


class PlayMode:
    def __init__(self, app: "NexisApp"):
        self.app = app
        self.is_playing = False
        self.is_paused = False
        self._snapshot = None
        self._last_time = 0.0
        self._pending_input: list = []  # (key, pressed) pairs queued between frames

    # ── Public ────────────────────────────────────────────────────────

    def play(self) -> None:
        if self.is_playing:
            return
        scene = self.app.active_scene
        if scene is None:
            self.app.console.warning("No active scene to play.")
            return

        self._snapshot = copy.deepcopy(scene.to_dict())
        self._init_physics(scene)

        # Ensure there's a camera
        from core.camera_auto import ensure_camera

        ensure_camera(scene, getattr(self.app, "project_type", "3D"))

        scene.start()
        self.is_playing = True
        self.is_paused = False
        self._last_time = time.perf_counter()
        self._pending_input.clear()

        mw = getattr(self.app, "main_window", None)
        if mw and hasattr(mw, "toolbar"):
            mw.toolbar.set_playing(True)
        self.app.console.info("▶ Play")

    def pause(self) -> None:
        if not self.is_playing:
            return
        self.is_paused = not self.is_paused
        mw = getattr(self.app, "main_window", None)
        if mw and hasattr(mw, "toolbar"):
            mw.toolbar.set_paused(self.is_paused)
        self.app.console.info("⏸ Paused" if self.is_paused else "▶ Resumed")

    def stop(self) -> None:
        if not self.is_playing:
            return
        scene = self.app.active_scene
        if scene:
            scene.stop()

        self.is_playing = False
        self.is_paused = False

        # Restore snapshot
        if self._snapshot and scene:
            from core.scene import Scene

            restored = Scene.from_dict(self._snapshot)
            self.app.active_scene = restored
            try:
                self.app.scene_manager.set_active(restored)
            except Exception:
                pass
            mw = getattr(self.app, "main_window", None)
            if mw:
                mw.hierarchy.refresh()
                mw.inspector.clear()
        self._snapshot = None

        mw = getattr(self.app, "main_window", None)
        if mw and hasattr(mw, "toolbar"):
            mw.toolbar.set_playing(False)
        self.app.console.info("⏹ Stop")

    # ── Per-frame update ─────────────────────────────────────────────

    def update(self) -> None:
        if not self.is_playing or self.is_paused:
            return

        now = time.perf_counter()
        dt = min(0.05, now - self._last_time)
        self._last_time = now

        from core.time_manager import Time

        Time._delta_time = dt
        Time._elapsed += dt
        Time._frame += 1

        scene = self.app.active_scene
        if scene is None:
            return

        # ── Physics step ─────────────────────────────────────────────
        pw = getattr(scene, "_physics_world", None)
        if pw is not None:
            pw.step(dt)
            self._sync_physics_to_transforms(scene, pw)
            self._fire_collision_callbacks(scene, pw)

        # ── Forward queued input to scripts ──────────────────────────
        if self._pending_input:
            from core.script_component import ScriptComponent

            for entity in scene.all_entities():
                if not entity.enabled:
                    continue
                sc = entity.get_component(ScriptComponent)
                if sc and sc._instance:
                    for key, pressed in self._pending_input:
                        try:
                            fn = getattr(sc._instance, "on_input", None)
                            if fn:
                                fn(entity, key, pressed)
                        except Exception as e:
                            self.app.console.error(
                                f"[{entity.name}] on_input error: {e}"
                            )
            self._pending_input.clear()

        # ── Script updates ────────────────────────────────────────────
        scene.update(dt)

    # ── Input forwarding ─────────────────────────────────────────────

    def send_input(self, key: int, pressed: bool) -> None:
        from core.input_manager import Input

        if pressed:
            Input.on_key_press(key)
        else:
            Input.on_key_release(key)
        self._pending_input.append((key, pressed))

    # ── Physics helpers ───────────────────────────────────────────────

    def _init_physics(self, scene) -> None:
        from core.physics_2d import (
            PhysicsWorld2D,
            Rigidbody2D,
            BoxCollider2D,
            CircleCollider2D,
        )

        gravity = (0.0, -9.81)
        try:
            ps = getattr(self.app.project, "settings", None)
            if ps:
                gravity = (
                    getattr(ps, "physics_gravity_x", 0.0),
                    getattr(ps, "physics_gravity_y", -9.81),
                )
        except Exception:
            pass

        pw = PhysicsWorld2D(gravity=gravity)

        for entity in scene.all_entities():
            rb = entity.get_component(Rigidbody2D)
            if rb is None:
                continue
            pos = entity.transform.position
            pw.add_body(
                entity.id,
                pos[0],
                pos[1],
                mass=rb.mass,
                is_kinematic=rb.is_kinematic,
                gravity_scale=rb.gravity_scale,
                drag=rb.drag,
            )
            box = entity.get_component(BoxCollider2D)
            cir = entity.get_component(CircleCollider2D)
            if box:
                pw.set_box_shape(entity.id, box.width, box.height, box.is_trigger)
            elif cir:
                pw.set_circle_shape(entity.id, cir.radius, cir.is_trigger)

        scene._physics_world = pw

    def _sync_physics_to_transforms(self, scene, pw) -> None:
        from core.physics_2d import Rigidbody2D

        for entity in scene.all_entities():
            rb = entity.get_component(Rigidbody2D)
            if rb is None:
                continue
            body = pw.get_body(entity.id)
            if body is None:
                continue
            entity.transform.position[0] = body.position[0]
            entity.transform.position[1] = body.position[1]
            entity.transform._dirty = True
            rb.velocity = list(body.velocity)

    def _fire_collision_callbacks(self, scene, pw) -> None:
        from core.script_component import ScriptComponent

        events = getattr(pw, "_collision_events", [])
        if not events:
            return
        for id_a, id_b, enter in list(events):
            for eid, other_eid in [(id_a, id_b), (id_b, id_a)]:
                entity = scene.get_entity_by_id(eid)
                other = scene.get_entity_by_id(other_eid)
                if entity is None or other is None:
                    continue
                sc = entity.get_component(ScriptComponent)
                if sc and sc._instance:
                    method = "on_collision_enter" if enter else "on_collision_exit"
                    fn = getattr(sc._instance, method, None)
                    if fn:
                        try:
                            fn(other)
                        except Exception as e:
                            self.app.console.error(
                                f"[{entity.name}] {method} error: {e}"
                            )
        pw._collision_events.clear()
