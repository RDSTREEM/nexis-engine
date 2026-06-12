from __future__ import annotations
import sys
import json
import time
import argparse
from pathlib import Path

import moderngl
from PySide6.QtCore import Qt, QEvent, QTimer
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtOpenGLWidgets import QOpenGLWidget


class GameWidget(QOpenGLWidget):
    def __init__(self, project_path: str, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()
        self.grabKeyboard()
        _app = QApplication.instance()
        if _app is not None:
            _app.installEventFilter(self)
        self.setMouseTracking(True)
        self._project_path = Path(project_path)
        self._ctx = None
        self._scene = None
        self._ready = False

        from core.console import EngineConsole
        from core.time_manager import Time
        from core.event_system import Events
        from core.input_manager import Input
        from core.physics_2d import PhysicsWorld2D

        self._console = EngineConsole()
        self._Time = Time
        self._Events = Events
        self._Input = Input
        self._physics = PhysicsWorld2D()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

    def initializeGL(self):
        self._ctx = moderngl.create_context()
        self._load_project()

    def _load_project(self):
        try:
            pdata = json.loads(self._project_path.read_text(encoding="utf-8"))
            startup = pdata.get("startup_scene", "")
            scene_path = self._project_path.parent / startup
            from core.scene import Scene

            self._scene = Scene.from_dict(
                json.loads(scene_path.read_text(encoding="utf-8"))
            )
            self._ptype = pdata.get("type", "3D")
            self._Time.start()
            self._init_physics()
            self._scene.start()
            self._ready = True
            self._console.info(f"Game started: {pdata.get('name','')}")
        except Exception as e:
            self._console.error(f"Failed to load project: {e}")
            import traceback

            traceback.print_exc()

    def paintGL(self):
        if not self._ready or self._scene is None:
            return
        w, h = max(1, self.width()), max(1, self.height())
        fbo = self._ctx.detect_framebuffer(self.defaultFramebufferObject())
        fbo.use()
        self._ctx.viewport = (0, 0, w, h)
        self._ctx.enable(moderngl.DEPTH_TEST)
        cam = self._scene._find_main_camera()
        if cam:
            cc = cam.clear_color
            self._ctx.clear(float(cc[0]), float(cc[1]), float(cc[2]), float(cc[3]))
            view = cam.get_view_matrix()
            proj = cam.get_projection_matrix(w, h)
            self._scene.render_editor(self._ctx, view, proj)
        else:
            self._ctx.clear(0.05, 0.05, 0.05, 1.0)

    def resizeGL(self, w, h):
        if self._ctx:
            self._ctx.viewport = (0, 0, w, h)

    def showEvent(self, event):
        self.setFocus()
        self.grabKeyboard()
        super().showEvent(event)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            self._Input.on_key_press(event.key())
            if self._scene:
                from core.script_component import ScriptComponent

                for e in self._scene.all_entities():
                    sc = e.get_component(ScriptComponent)
                    if sc and sc._loaded:
                        sc.on_input(event.key(), True)
        elif event.type() == QEvent.KeyRelease:
            self._Input.on_key_release(event.key())
            if self._scene:
                from core.script_component import ScriptComponent

                for e in self._scene.all_entities():
                    sc = e.get_component(ScriptComponent)
                    if sc and sc._loaded:
                        sc.on_input(event.key(), False)
        return super().eventFilter(obj, event)

    def _tick(self):
        if not self._ready:
            return
        self._Input.begin_frame()
        dt = self._Time.tick()

        self._scene.update(dt)

        self._sync_script_velocity_to_physics()

        self._physics.step(dt)

        self._sync_physics_to_transforms()
        self._fire_collision_callbacks()

        self.update()

    def _init_physics(self) -> None:
        from core.physics_2d import Rigidbody2D, BoxCollider2D, CircleCollider2D

        if self._scene is None:
            return
        self._physics = type(self._physics)(gravity=self._physics.gravity)
        for entity in self._scene.all_entities():
            rb = entity.get_component(Rigidbody2D)
            if rb is None:
                continue
            pos = entity.transform.position
            self._physics.add_body(
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
                self._physics.set_box_shape(
                    entity.id, box.width, box.height, box.is_trigger
                )
            elif cir:
                self._physics.set_circle_shape(entity.id, cir.radius, cir.is_trigger)
        self._scene._physics_world = self._physics

    def _sync_script_velocity_to_physics(self) -> None:
        from core.physics_2d import Rigidbody2D

        if self._scene is None:
            return
        for entity in self._scene.all_entities():
            rb = entity.get_component(Rigidbody2D)
            if rb is None:
                continue
            body = self._physics.get_body(entity.id)
            if body is None:
                continue
            body.velocity[0] = rb.velocity[0]
            body.velocity[1] = rb.velocity[1]

    def _sync_physics_to_transforms(self) -> None:
        from core.physics_2d import Rigidbody2D

        if self._scene is None:
            return
        for entity in self._scene.all_entities():
            rb = entity.get_component(Rigidbody2D)
            if rb is None:
                continue
            body = self._physics.get_body(entity.id)
            if body is None:
                continue
            entity.transform.position[0] = body.position[0]
            entity.transform.position[1] = body.position[1]
            entity.transform._dirty = True
            rb.velocity[0] = body.velocity[0]
            rb.velocity[1] = body.velocity[1]

    def _fire_collision_callbacks(self) -> None:
        from core.script_component import ScriptComponent

        if self._scene is None:
            return
        events = getattr(self._physics, "_collision_events", [])
        if not events:
            return
        for id_a, id_b, enter in list(events):
            for eid, other_eid in [(id_a, id_b), (id_b, id_a)]:
                entity = self._scene.get_entity_by_id(eid)
                other = self._scene.get_entity_by_id(other_eid)
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
                            self._console.error(f"[{entity.name}] {method} error: {e}")
        self._physics._collision_events.clear()

    def mousePressEvent(self, ev):
        self.setFocus()
        self._Input.on_mouse_press(ev.button().value)

    def mouseReleaseEvent(self, ev):
        self._Input.on_mouse_release(ev.button().value)

    def mouseMoveEvent(self, ev):
        pos = ev.position().toPoint()
        self._Input.on_mouse_move(pos.x(), pos.y())

    def wheelEvent(self, ev):
        self._Input.on_scroll(ev.angleDelta().y() / 120.0)

    def closeEvent(self, ev):
        if self._scene:
            self._scene.stop()
        self._Events.clear()
        self._Time.stop()
        super().closeEvent(ev)


class PlayWindow(QMainWindow):
    def __init__(self, project_path: str):
        super().__init__()
        self.setWindowTitle("NEXIS — Game")
        self.resize(960, 540)
        self._widget = GameWidget(project_path, parent=self)
        self.setCentralWidget(self._widget)

    @staticmethod
    def launch(project_path: str) -> "PlayWindow":
        win = PlayWindow(project_path)
        win.show()
        return win


def main():
    parser = argparse.ArgumentParser(description="NEXIS Game Runner")
    parser.add_argument("project", help="Path to .nexis project file")
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=540)
    parser.add_argument("--title", default="")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    win = QMainWindow()
    win.setWindowTitle(args.title or Path(args.project).stem)
    win.resize(args.width, args.height)
    widget = GameWidget(args.project)
    win.setCentralWidget(widget)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
