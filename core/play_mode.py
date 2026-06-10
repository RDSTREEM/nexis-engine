"""
play_mode.py
FIX: Physics world is now ticked every frame during play.
FIX: Rigidbody2D body positions are synced back to entity transforms.
FIX: Collision callbacks (on_collision_enter) are fired to script components.
"""
from __future__ import annotations
import copy
import time
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app import NexisApp


class PlayMode:
    def __init__(self, app: "NexisApp"):
        self.app        = app
        self.is_playing = False
        self.is_paused  = False
        self._snapshot  = None      # deep copy of scene before play
        self._last_time = 0.0

    # ------------------------------------------------------------------

    def play(self) -> None:
        if self.is_playing:
            return
        scene = self.app.active_scene
        if scene is None:
            return

        # Snapshot scene state
        self._snapshot = copy.deepcopy(scene.to_dict())

        # Init physics world
        self._init_physics(scene)

        # Start all entity scripts
        scene.start()

        self.is_playing = True
        self.is_paused  = False
        self._last_time = time.perf_counter()

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
        state = "⏸ Paused" if self.is_paused else "▶ Resumed"
        self.app.console.info(state)

    def stop(self) -> None:
        if not self.is_playing:
            return
        scene = self.app.active_scene
        if scene:
            scene.stop()

        self.is_playing = False
        self.is_paused  = False

        # Restore snapshot
        if self._snapshot and scene:
            from core.scene import Scene
            restored = Scene.from_dict(self._snapshot)
            self.app.active_scene = restored
            self.app.scene_manager.set_active(restored)
            mw = getattr(self.app, "main_window", None)
            if mw:
                mw.hierarchy.refresh()
                mw.inspector.clear()
        self._snapshot = None

        mw = getattr(self.app, "main_window", None)
        if mw and hasattr(mw, "toolbar"):
            mw.toolbar.set_playing(False)
        self.app.console.info("⏹ Stop")

    # ------------------------------------------------------------------

    def update(self) -> None:
        if not self.is_playing or self.is_paused:
            return

        now = time.perf_counter()
        dt  = min(0.05, now - self._last_time)
        self._last_time = now

        from core.time_manager import Time
        Time._delta_time = dt
        Time._elapsed   += dt
        Time._frame     += 1

        scene = self.app.active_scene
        if scene is None:
            return

        # ── FIX: Step physics world ──────────────────────────────────────
        pw = getattr(scene, "_physics_world", None)
        if pw is not None:
            pw.step(dt)
            self._sync_physics_to_transforms(scene, pw)
            self._fire_collision_callbacks(scene, pw)

        # Update scripts
        scene.update(dt)

    # ------------------------------------------------------------------
    # Physics helpers
    # ------------------------------------------------------------------

    def _init_physics(self, scene) -> None:
        """Create/reset the PhysicsWorld2D and register all Rigidbody2D bodies."""
        from core.physics_2d import PhysicsWorld2D, Rigidbody2D, BoxCollider2D, CircleCollider2D
        gravity = (0.0, -9.81)
        try:
            from core.project_settings import ProjectSettings
            ps = self.app.project.settings
            if ps:
                gravity = (ps.physics_gravity_x, ps.physics_gravity_y)
        except Exception:
            pass

        pw = PhysicsWorld2D(gravity=gravity)

        for entity in scene.all_entities():
            rb = entity.get_component(Rigidbody2D)
            if rb is None:
                continue
            pos = entity.transform.position
            pw.add_body(entity.id, pos[0], pos[1],
                        mass=rb.mass,
                        is_kinematic=rb.is_kinematic,
                        gravity_scale=rb.gravity_scale,
                        drag=rb.drag)

            # Register collider shape
            box = entity.get_component(BoxCollider2D)
            cir = entity.get_component(CircleCollider2D)
            if box:
                pw.set_box_shape(entity.id, box.width, box.height, box.is_trigger)
            elif cir:
                pw.set_circle_shape(entity.id, cir.radius, cir.is_trigger)

        scene._physics_world = pw

    def _sync_physics_to_transforms(self, scene, pw) -> None:
        """
        FIX: Copy Rigidbody2D physics positions back to entity transforms.
        Without this, physics runs but entities don't visually move.
        """
        from core.physics_2d import Rigidbody2D
        for entity in scene.all_entities():
            rb = entity.get_component(Rigidbody2D)
            if rb is None:
                continue
            body = pw.get_body(entity.id)
            if body is None:
                continue
            # Write physics position → transform
            entity.transform.position[0] = body.position[0]
            entity.transform.position[1] = body.position[1]
            entity.transform._dirty = True
            # Also sync velocity back to rb for script access
            rb.velocity = list(body.velocity)

    def _fire_collision_callbacks(self, scene, pw) -> None:
        """
        FIX: Fire on_collision_enter/on_collision_exit on ScriptComponents
        when the physics world reports collisions this frame.
        """
        from core.script_component import ScriptComponent
        if not hasattr(pw, "_collision_events"):
            return
        for (id_a, id_b, enter) in pw._collision_events:
            for eid, other_eid in [(id_a, id_b), (id_b, id_a)]:
                entity = scene.get_entity_by_id(eid)
                other  = scene.get_entity_by_id(other_eid)
                if entity is None or other is None:
                    continue
                sc = entity.get_component(ScriptComponent)
                if sc and sc._instance:
                    try:
                        method = "on_collision_enter" if enter else "on_collision_exit"
                        fn = getattr(sc._instance, method, None)
                        if fn:
                            fn(other)
                    except Exception as e:
                        self.app.console.error(
                            f"[{entity.name}] collision callback error: {e}")
        pw._collision_events.clear()

    # ------------------------------------------------------------------

    def send_input(self, key: int, pressed: bool) -> None:
        from core.input_manager import Input
        if pressed:
            Input.on_key_press(key)
        else:
            Input.on_key_release(key)
