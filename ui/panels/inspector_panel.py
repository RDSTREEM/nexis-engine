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
        ne.textChanged.connect(
            lambda v: (setattr(e, "name", v), self.app.main_window.hierarchy.refresh())
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
        from core.sprite_renderer import SpriteRenderer
        from core.camera_component import CameraComponent
        import core.primitives as prim

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
            combo.addItems(list(prim.PRIMITIVES.keys()))
            combo.setCurrentText(comp.primitive)
            combo.currentTextChanged.connect(comp.set_primitive)
            form.addRow("Primitive", combo)
            self._material_rows(form, comp.material)

        elif isinstance(comp, SpriteRenderer):
            self._material_rows(form, comp.material)
            ws = QDoubleSpinBox()
            ws.setRange(0.01, 9999)
            ws.setValue(float(comp.size[0]))
            hs = QDoubleSpinBox()
            hs.setRange(0.01, 9999)
            hs.setValue(float(comp.size[1]))
            ws.valueChanged.connect(lambda v: comp.set_size(v, comp.size[1]))
            hs.valueChanged.connect(lambda v: comp.set_size(comp.size[0], v))
            form.addRow("Width", ws)
            form.addRow("Height", hs)

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

        self._layout.addLayout(form)
        self._layout.addWidget(_hline())

    def _material_rows(self, form, mat):
        c = mat.color
        btn = QPushButton()
        btn.setStyleSheet(
            f"background:rgb({int(c[0]*255)},{int(c[1]*255)},{int(c[2]*255)});"
        )

        def pick():
            dlg = QColorDialog()
            if dlg.exec():
                q = dlg.selectedColor()
                mat.set_color(q.redF(), q.greenF(), q.blueF(), q.alphaF())
                btn.setStyleSheet(f"background:rgb({q.red()},{q.green()},{q.blue()});")

        btn.clicked.connect(pick)
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
        opts = ["MeshRenderer", "SpriteRenderer", "CameraComponent"]
        choice, ok = QInputDialog.getItem(
            self, "Add Component", "Type:", opts, 0, False
        )
        if not ok:
            return
        from core.mesh_renderer import MeshRenderer
        from core.sprite_renderer import SpriteRenderer
        from core.camera_component import CameraComponent

        m = {
            "MeshRenderer": MeshRenderer,
            "SpriteRenderer": SpriteRenderer,
            "CameraComponent": CameraComponent,
        }
        cls = m.get(choice)
        if cls:
            self._entity.add_component(cls())
            self._rebuild()
