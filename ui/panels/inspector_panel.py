from __future__ import annotations
from typing import Optional

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDockWidget,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QFrame,
    QFileDialog,
)


def _hline() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.HLine)
    f.setFrameShadow(QFrame.Sunken)
    return f


def _section(text: str) -> QLabel:
    l = QLabel(text)
    l.setStyleSheet("font-weight:bold;font-size:11px;color:#aaaaaa;")
    return l


class Vec3Widget(QWidget):
    def __init__(self, label: str, value: np.ndarray, callback, parent=None):
        super().__init__(parent)
        self._cb = callback
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(QLabel(label))
        self._spins = []
        for i, axis in enumerate("XYZ"):
            sb = QDoubleSpinBox()
            sb.setRange(-99999, 99999)
            sb.setDecimals(3)
            sb.setSingleStep(0.1)
            sb.setValue(float(value[i]))
            sb.setPrefix(f"{axis} ")
            sb.valueChanged.connect(lambda v, i=i: self._changed(i, v))
            row.addWidget(sb)
            self._spins.append(sb)

    def _changed(self, idx, val):
        self._cb(idx, val)

    def refresh(self, value: np.ndarray):
        for i, sb in enumerate(self._spins):
            sb.blockSignals(True)
            sb.setValue(float(value[i]))
            sb.blockSignals(False)


class InspectorPanel(QDockWidget):
    def __init__(self, app, parent=None):
        super().__init__("Inspector", parent)
        self.app = app
        self._entity = None
        self._rebuilding = False  # re-entrant guard
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._content = QWidget()
        self._layout = QVBoxLayout(self._content)
        self._layout.setAlignment(Qt.AlignTop)
        self._layout.setSpacing(4)
        scroll.setWidget(self._content)
        self.setWidget(scroll)
        self._show_empty()

    # ------------------------------------------------------------------

    def show_entity(self, entity) -> None:
        if entity is None:
            self.clear()
            return
        self._entity = entity
        self._rebuild()

    def clear(self) -> None:
        self._entity = None
        self._rebuild()

    def _clear_layout(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _show_empty(self):
        self._clear_layout()
        lbl = QLabel("Select an entity to inspect.")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("color:#666;")
        self._layout.addWidget(lbl)

    def _rebuild(self):
        if self._rebuilding:
            return
        self._rebuilding = True
        try:
            self._do_rebuild()
        finally:
            self._rebuilding = False

    def _do_rebuild(self):
        if self._entity is None:
            self._show_empty()
            return
        self._clear_layout()
        self._build_header()
        self._build_transform()
        from core.transform import Transform

        for comp in self._entity.components:
            if not isinstance(comp, Transform):
                self._build_component(comp)
        self._layout.addWidget(self._add_comp_btn())

    # --- header ---
    def _build_header(self):
        e = self._entity
        row = QHBoxLayout()
        cb = QCheckBox()
        cb.setChecked(e.enabled)
        cb.toggled.connect(lambda v: setattr(e, "enabled", v))
        row.addWidget(cb)
        ne = QLineEdit(e.name)
        # use editingFinished so we only update on Enter/focus-loss
        # not on every keystroke (which caused re-entrant rebuilds)
        ne.editingFinished.connect(
            lambda: (
                setattr(e, "name", ne.text()),
                self.app.main_window.hierarchy.refresh(),
            )
        )
        row.addWidget(ne)
        self._layout.addLayout(row)
        self._layout.addWidget(_hline())

    # --- transform ---
    def _build_transform(self):
        t = self._entity.transform
        self._layout.addWidget(_section("Transform"))

        def _mk(label, arr):
            def cb(idx, val):
                arr[idx] = val
                t._dirty = True

            return Vec3Widget(label, arr, cb)

        self._layout.addWidget(_mk("Pos", t.position))
        self._layout.addWidget(_mk("Rot", t.rotation))
        self._layout.addWidget(_mk("Scl", t.scale))
        self._layout.addWidget(_hline())

    # --- generic component ---
    def _build_component(self, comp):
        from core.mesh_renderer import MeshRenderer
        from core.sprite_renderer import SpriteRenderer, Shape2DRenderer
        from core.camera_component import CameraComponent
        from core.physics_2d import BoxCollider2D, CircleCollider2D, Rigidbody2D
        from core.script_component import ScriptComponent
        from core.audio_source import AudioSource
        import core.primitives as prim3d
        import core.primitives_2d as prim2d

        hrow = QHBoxLayout()
        cb = QCheckBox()
        cb.setChecked(comp.enabled)
        cb.toggled.connect(lambda v: setattr(comp, "enabled", v))
        hrow.addWidget(cb)
        hrow.addWidget(_section(type(comp).__name__))
        hrow.addStretch()
        x = QPushButton("✕")
        x.setFixedSize(20, 20)
        x.setStyleSheet("color:#f55;border:none;")
        x.clicked.connect(lambda: self._remove(comp))
        hrow.addWidget(x)
        self._layout.addLayout(hrow)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)

        if isinstance(comp, MeshRenderer):
            combo = QComboBox()
            combo.addItems(list(prim3d.PRIMITIVES.keys()))
            combo.setCurrentText(comp.primitive)
            combo.currentTextChanged.connect(comp.set_primitive)
            form.addRow("Primitive", combo)
            self._material_rows(form, comp.material)

        elif isinstance(comp, Shape2DRenderer):
            combo = QComboBox()
            combo.addItems(list(prim2d.PRIMITIVES_2D.keys()))
            combo.setCurrentText(comp.shape)
            combo.currentTextChanged.connect(comp.set_shape)
            form.addRow("Shape", combo)
            w = QDoubleSpinBox()
            w.setRange(0.01, 9999)
            w.setValue(float(comp.size[0]))
            h = QDoubleSpinBox()
            h.setRange(0.01, 9999)
            h.setValue(float(comp.size[1]))
            w.valueChanged.connect(lambda v: comp.set_size(v, comp.size[1]))
            h.valueChanged.connect(lambda v: comp.set_size(comp.size[0], v))
            form.addRow("Width", w)
            form.addRow("Height", h)
            # colour picker
            btn = self._color_btn(
                comp.color, lambda r, g, b, a: comp.set_color(r, g, b, a)
            )
            form.addRow("Color", btn)

        elif isinstance(comp, SpriteRenderer):
            combo = QComboBox()
            combo.addItems(list(prim2d.PRIMITIVES_2D.keys()))
            combo.setCurrentText(comp.shape)
            combo.currentTextChanged.connect(comp.set_shape)
            form.addRow("Shape", combo)
            self._material_rows(form, comp.material)
            w = QDoubleSpinBox()
            w.setRange(0.01, 9999)
            w.setValue(float(comp.size[0]))
            h = QDoubleSpinBox()
            h.setRange(0.01, 9999)
            h.setValue(float(comp.size[1]))
            w.valueChanged.connect(lambda v: comp.set_size(v, comp.size[1]))
            h.valueChanged.connect(lambda v: comp.set_size(comp.size[0], v))
            form.addRow("Width", w)
            form.addRow("Height", h)
            fx = QCheckBox()
            fx.setChecked(comp.flip_x)
            fx.toggled.connect(
                lambda v: setattr(comp, "flip_x", v) or setattr(comp, "_vao", None)
            )
            fy = QCheckBox()
            fy.setChecked(comp.flip_y)
            fy.toggled.connect(
                lambda v: setattr(comp, "flip_y", v) or setattr(comp, "_vao", None)
            )
            form.addRow("Flip X", fx)
            form.addRow("Flip Y", fy)

        elif isinstance(comp, CameraComponent):
            pc = QComboBox()
            pc.addItems(["perspective", "orthographic"])
            pc.setCurrentText(comp.projection)
            pc.currentTextChanged.connect(lambda v: setattr(comp, "projection", v))
            form.addRow("Projection", pc)
            fov = QDoubleSpinBox()
            fov.setRange(10, 170)
            fov.setValue(comp.fov)
            fov.valueChanged.connect(lambda v: setattr(comp, "fov", v))
            form.addRow("FOV", fov)
            near = QDoubleSpinBox()
            near.setRange(0.001, 100)
            near.setDecimals(3)
            near.setValue(comp.near)
            near.valueChanged.connect(lambda v: setattr(comp, "near", v))
            form.addRow("Near", near)
            far = QDoubleSpinBox()
            far.setRange(1, 100000)
            far.setValue(comp.far)
            far.valueChanged.connect(lambda v: setattr(comp, "far", v))
            form.addRow("Far", far)
            mc = QCheckBox()
            mc.setChecked(comp.is_main)
            mc.toggled.connect(lambda v: setattr(comp, "is_main", v))
            form.addRow("Main Cam", mc)

        elif isinstance(comp, BoxCollider2D):
            ws = QDoubleSpinBox()
            ws.setRange(0.01, 9999)
            ws.setValue(comp.width)
            ws.valueChanged.connect(lambda v: setattr(comp, "width", v))
            hs = QDoubleSpinBox()
            hs.setRange(0.01, 9999)
            hs.setValue(comp.height)
            hs.valueChanged.connect(lambda v: setattr(comp, "height", v))
            trig = QCheckBox()
            trig.setChecked(comp.is_trigger)
            trig.toggled.connect(lambda v: setattr(comp, "is_trigger", v))
            form.addRow("Width", ws)
            form.addRow("Height", hs)
            form.addRow("Trigger", trig)

        elif isinstance(comp, CircleCollider2D):
            rs = QDoubleSpinBox()
            rs.setRange(0.001, 9999)
            rs.setValue(comp.radius)
            rs.valueChanged.connect(lambda v: setattr(comp, "radius", v))
            trig = QCheckBox()
            trig.setChecked(comp.is_trigger)
            trig.toggled.connect(lambda v: setattr(comp, "is_trigger", v))
            form.addRow("Radius", rs)
            form.addRow("Trigger", trig)

        elif isinstance(comp, Rigidbody2D):
            gs = QDoubleSpinBox()
            gs.setRange(-10, 10)
            gs.setValue(comp.gravity_scale)
            gs.valueChanged.connect(lambda v: setattr(comp, "gravity_scale", v))
            dr = QDoubleSpinBox()
            dr.setRange(0, 1)
            dr.setSingleStep(0.01)
            dr.setValue(comp.drag)
            dr.valueChanged.connect(lambda v: setattr(comp, "drag", v))
            ms = QDoubleSpinBox()
            ms.setRange(0.001, 9999)
            ms.setValue(comp.mass)
            ms.valueChanged.connect(lambda v: setattr(comp, "mass", v))
            kin = QCheckBox()
            kin.setChecked(comp.is_kinematic)
            kin.toggled.connect(lambda v: setattr(comp, "is_kinematic", v))
            form.addRow("Gravity Scale", gs)
            form.addRow("Drag", dr)
            form.addRow("Mass", ms)
            form.addRow("Kinematic", kin)

        elif isinstance(comp, AudioSource):
            vol = QDoubleSpinBox()
            vol.setRange(0, 1)
            vol.setSingleStep(0.05)
            vol.setValue(comp.volume)
            vol.valueChanged.connect(lambda v: setattr(comp, "volume", v))
            form.addRow("Volume", vol)

            pitch = QDoubleSpinBox()
            pitch.setRange(0.1, 4)
            pitch.setSingleStep(0.1)
            pitch.setValue(comp.pitch)
            pitch.valueChanged.connect(lambda v: setattr(comp, "pitch", v))
            form.addRow("Pitch", pitch)

            loop_cb = QCheckBox()
            loop_cb.setChecked(comp.loop)
            loop_cb.toggled.connect(lambda v: setattr(comp, "loop", v))
            form.addRow("Loop", loop_cb)

            pos_cb = QCheckBox()
            pos_cb.setChecked(comp.play_on_start)
            pos_cb.toggled.connect(lambda v: setattr(comp, "play_on_start", v))
            form.addRow("Play On Start", pos_cb)

            play_btn = QPushButton("▶ Preview")
            play_btn.clicked.connect(lambda: comp.play() if comp.clip else None)
            stop_btn = QPushButton("⏹ Stop")
            stop_btn.clicked.connect(comp.stop)
            pbrow = QHBoxLayout()
            pbrow.addWidget(play_btn)
            pbrow.addWidget(stop_btn)
            pbw = QWidget()
            pbw.setLayout(pbrow)
            form.addRow("", pbw)

        elif isinstance(comp, ScriptComponent):
            path_lbl = QLabel(comp.script_path or "(none)")
            path_lbl.setWordWrap(True)
            path_lbl.setStyleSheet("color:#888;font-size:10px;")
            form.addRow("Script", path_lbl)
            browse = QPushButton("Browse…")

            def _pick():
                p, _ = QFileDialog.getOpenFileName(
                    self,
                    "Select Script",
                    str(self.app.project.project_root or ""),
                    "Scripts (*.py *.amh);;All (*)",
                )
                if p:
                    comp.script_path = p
                    path_lbl.setText(p)
                    comp.reload()

            browse.clicked.connect(_pick)
            reload_btn = QPushButton("↺ Reload")
            reload_btn.clicked.connect(lambda: comp.reload())
            form.addRow("", browse)
            form.addRow("", reload_btn)
            if comp._error:
                err = QLabel(comp._error[:200])
                err.setStyleSheet("color:#f55;font-size:9px;")
                err.setWordWrap(True)
                form.addRow("Error", err)

        self._layout.addLayout(form)
        self._layout.addWidget(_hline())

    # ------------------------------------------------------------------

    def _color_btn(self, color_arr, on_change):
        btn = QPushButton()
        c = color_arr
        btn.setStyleSheet(
            f"background:rgb({int(c[0]*255)},{int(c[1]*255)},{int(c[2]*255)});"
        )

        def pick():
            dlg = QColorDialog()
            if dlg.exec():
                q = dlg.selectedColor()
                on_change(q.redF(), q.greenF(), q.blueF(), q.alphaF())
                btn.setStyleSheet(f"background:rgb({q.red()},{q.green()},{q.blue()});")

        btn.clicked.connect(pick)
        return btn

    def _material_rows(self, form, mat):
        btn = self._color_btn(mat.color, lambda r, g, b, a: mat.set_color(r, g, b, a))
        form.addRow("Color", btn)
        amb = QDoubleSpinBox()
        amb.setRange(0, 1)
        amb.setSingleStep(0.05)
        amb.setValue(mat.ambient)
        amb.valueChanged.connect(lambda v: setattr(mat, "ambient", v))
        form.addRow("Ambient", amb)

    def _remove(self, comp):
        if self._entity:
            self._entity.remove_component(comp)
            self._rebuild()

    def _add_comp_btn(self):
        btn = QPushButton("+ Add Component")
        btn.clicked.connect(self._on_add)
        return btn

    def _on_add(self):
        if not self._entity:
            return
        opts = [
            "MeshRenderer",
            "SpriteRenderer",
            "Shape2DRenderer",
            "CameraComponent",
            "BoxCollider2D",
            "CircleCollider2D",
            "Rigidbody2D",
            "ScriptComponent",
        ]
        choice, ok = QInputDialog.getItem(
            self, "Add Component", "Type:", opts, 0, False
        )
        if not ok:
            return
        from core.mesh_renderer import MeshRenderer
        from core.sprite_renderer import SpriteRenderer, Shape2DRenderer
        from core.camera_component import CameraComponent
        from core.physics_2d import BoxCollider2D, CircleCollider2D, Rigidbody2D
        from core.script_component import ScriptComponent
        from core.audio_source import AudioSource

        m = {
            "MeshRenderer": MeshRenderer,
            "SpriteRenderer": SpriteRenderer,
            "Shape2DRenderer": Shape2DRenderer,
            "CameraComponent": CameraComponent,
            "BoxCollider2D": BoxCollider2D,
            "CircleCollider2D": CircleCollider2D,
            "Rigidbody2D": Rigidbody2D,
            "ScriptComponent": ScriptComponent,
            "AudioSource": AudioSource,
        }
        cls = m.get(choice)
        if cls:
            self._entity.add_component(cls())
            self._rebuild()
