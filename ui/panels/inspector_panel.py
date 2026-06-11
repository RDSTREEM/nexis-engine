"""
inspector_panel.py — Complete rework.
Clean card-based layout: each component is a collapsible card.
Texture assignment wired directly in material rows.
Re-entrant guard + editingFinished on name field.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional

import numpy as np
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDockWidget,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

# ── helpers ───────────────────────────────────────────────────────────────


def _hline():
    f = QFrame()
    f.setFrameShape(QFrame.HLine)
    f.setStyleSheet("color:#3a3a3a;")
    return f


class _Card(QWidget):
    """A collapsible component card with a header bar."""

    def __init__(self, title: str, on_remove=None, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            _Card { background:#303030; border-radius:5px; }
        """)
        self._collapsed = False
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── header ────────────────────────────────────────────────────────
        header = QWidget()
        header.setFixedHeight(28)
        header.setStyleSheet("background:#252525; border-radius:5px 5px 0 0;")
        hrow = QHBoxLayout(header)
        hrow.setContentsMargins(8, 0, 6, 0)
        hrow.setSpacing(4)

        self._arrow = QLabel("▾")
        self._arrow.setStyleSheet("color:#888; font-size:10px;")
        self._arrow.setFixedWidth(14)
        hrow.addWidget(self._arrow)

        self._title_lbl = QLabel(title)
        self._title_lbl.setStyleSheet("color:#ccc; font-weight:600; font-size:11px;")
        hrow.addWidget(self._title_lbl, 1)

        if on_remove:
            rm = QPushButton("✕")
            rm.setFixedSize(18, 18)
            rm.setStyleSheet(
                "QPushButton{color:#888;border:none;background:transparent;font-size:11px;}"
                "QPushButton:hover{color:#f55;}"
            )
            rm.clicked.connect(on_remove)
            hrow.addWidget(rm)

        header.mousePressEvent = lambda _e: self._toggle()
        outer.addWidget(header)

        # ── body ──────────────────────────────────────────────────────────
        self._body = QWidget()
        self._body.setStyleSheet("background:#2c2c2c; border-radius:0 0 5px 5px;")
        outer.addWidget(self._body)

    def body_layout(self) -> QVBoxLayout:
        if not self._body.layout():
            lay = QVBoxLayout(self._body)
            lay.setContentsMargins(10, 8, 10, 8)
            lay.setSpacing(6)
        return self._body.layout()

    def _toggle(self):
        self._collapsed = not self._collapsed
        self._body.setVisible(not self._collapsed)
        self._arrow.setText("▸" if self._collapsed else "▾")


class _FormRow(QWidget):
    """Label + widget in a compact horizontal row."""

    def __init__(self, label: str, widget: QWidget, parent=None):
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        lbl = QLabel(label)
        lbl.setStyleSheet("color:#999; font-size:10px;")
        lbl.setFixedWidth(72)
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        row.addWidget(lbl)
        row.addWidget(widget, 1)


def _spin(lo, hi, val, decimals=3, step=0.1, on_change=None):
    sb = QDoubleSpinBox()
    sb.setRange(lo, hi)
    sb.setDecimals(decimals)
    sb.setSingleStep(step)
    sb.setValue(float(val))
    sb.setStyleSheet(
        "QDoubleSpinBox{background:#1e1e1e;border:1px solid #3a3a3a;"
        "border-radius:3px;padding:1px 4px;color:#ddd;font-size:10px;}"
    )
    if on_change:
        sb.valueChanged.connect(on_change)
    return sb


def _check(val: bool, label: str = "", on_change=None):
    cb = QCheckBox(label)
    cb.setChecked(val)
    cb.setStyleSheet("QCheckBox{color:#bbb;font-size:10px;}")
    if on_change:
        cb.toggled.connect(on_change)
    return cb


def _combo(items: list, current: str, on_change=None):
    c = QComboBox()
    c.addItems(items)
    c.setCurrentText(current)
    c.setStyleSheet(
        "QComboBox{background:#1e1e1e;border:1px solid #3a3a3a;"
        "border-radius:3px;padding:1px 4px;color:#ddd;font-size:10px;}"
    )
    if on_change:
        c.currentTextChanged.connect(on_change)
    return c


class _Vec3Row(QWidget):
    """X/Y/Z inline spinboxes."""

    def __init__(self, arr: np.ndarray, on_change, parent=None):
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(4)
        labels = ["X", "Y", "Z"]
        colors = ["#cc4444", "#44cc44", "#4488cc"]
        for i in range(3):
            lbl = QLabel(labels[i])
            lbl.setStyleSheet(f"color:{colors[i]};font-size:10px;font-weight:bold;")
            lbl.setFixedWidth(12)
            sb = QDoubleSpinBox()
            sb.setRange(-99999, 99999)
            sb.setDecimals(3)
            sb.setSingleStep(0.1)
            sb.setValue(float(arr[i]))
            sb.setStyleSheet(
                "QDoubleSpinBox{background:#1e1e1e;border:1px solid #3a3a3a;"
                "border-radius:3px;padding:1px 3px;color:#ddd;font-size:10px;}"
            )
            sb.valueChanged.connect(lambda v, idx=i: on_change(idx, v))
            row.addWidget(lbl)
            row.addWidget(sb, 1)


# ── Main panel ────────────────────────────────────────────────────────────


class InspectorPanel(QDockWidget):
    def __init__(self, app, parent=None):
        super().__init__("Inspector", parent)
        self.app = app
        self._entity = None
        self._rebuilding = False
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.setMinimumWidth(240)

        # Scroll area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet("QScrollArea{border:none;background:#282828;}")

        self._root = QWidget()
        self._root.setStyleSheet("background:#282828;")
        self._vbox = QVBoxLayout(self._root)
        self._vbox.setContentsMargins(6, 6, 6, 6)
        self._vbox.setSpacing(6)
        self._vbox.setAlignment(Qt.AlignTop)
        self._scroll.setWidget(self._root)
        self.setWidget(self._scroll)
        self._show_empty()

    # ── Public ────────────────────────────────────────────────────────────

    def show_entity(self, entity) -> None:
        if entity is None:
            self.clear()
            return
        self._entity = entity
        self._rebuild()

    def clear(self) -> None:
        self._entity = None
        self._rebuild()

    # ── Internal ──────────────────────────────────────────────────────────

    def _clear(self):
        while self._vbox.count():
            item = self._vbox.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _show_empty(self):
        self._clear()
        lbl = QLabel("No entity selected")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("color:#555; font-size:11px; padding:20px;")
        self._vbox.addWidget(lbl)

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
        self._clear()
        self._build_entity_header()
        self._build_transform_card()
        from core.transform import Transform

        for comp in self._entity.components:
            if not isinstance(comp, Transform):
                self._build_component_card(comp)
        self._build_add_button()

    # ── Entity header ─────────────────────────────────────────────────────

    def _build_entity_header(self):
        e = self._entity
        card = QWidget()
        card.setStyleSheet("background:#1e1e1e; border-radius:5px;")
        row = QHBoxLayout(card)
        row.setContentsMargins(8, 6, 8, 6)
        row.setSpacing(8)

        en_cb = QCheckBox()
        en_cb.setChecked(e.enabled)
        en_cb.setToolTip("Entity enabled")
        en_cb.toggled.connect(lambda v: setattr(e, "enabled", v))
        row.addWidget(en_cb)

        name_edit = QLineEdit(e.name)
        name_edit.setStyleSheet(
            "QLineEdit{background:#2a2a2a;border:1px solid #3c3c3c;"
            "border-radius:3px;color:#fff;font-size:12px;font-weight:600;"
            "padding:3px 6px;}"
        )

        def _commit():
            new = name_edit.text().strip()
            if new and new != e.name:
                e.name = new
                mw = getattr(self.app, "main_window", None)
                if mw:
                    mw.hierarchy.refresh()

        name_edit.editingFinished.connect(_commit)
        row.addWidget(name_edit, 1)

        # Tags button - opens tag selection dialog
        tag_btn = QPushButton("Tags")
        tag_btn.setFixedWidth(50)
        tag_btn.setStyleSheet(
            "QPushButton{background:#1e3a1e;border:1px solid #2d6b2d;"
            "color:#55cc55;font-size:9px;border-radius:3px;padding:2px 6px;}"
            "QPushButton:hover{background:#254a25;}"
        )

        def _edit_tags():
            from ui.panels.tag_selector import TagSelectorDialog

            dlg = TagSelectorDialog(e.tags, self.app.project, self)
            if dlg.exec():
                e.tags = dlg.selected_tags
                tag_btn.setText(f"Tags ({len(e.tags)})" if e.tags else "Tags")

        tag_btn.clicked.connect(_edit_tags)
        row.addWidget(tag_btn)

        self._vbox.addWidget(card)

    # ── Transform card ────────────────────────────────────────────────────

    def _build_transform_card(self):
        t = self._entity.transform
        card = _Card("Transform")
        bl = card.body_layout()

        for label, arr in [
            ("Position", t.position),
            ("Rotation", t.rotation),
            ("Scale", t.scale),
        ]:

            def _cb(idx, val, a=arr):
                a[idx] = val
                t._dirty = True

            bl.addWidget(_FormRow(label, _Vec3Row(arr, _cb)))

        self._vbox.addWidget(card)

    # ── Component cards ───────────────────────────────────────────────────

    def _build_component_card(self, comp):
        from core.mesh_renderer import MeshRenderer
        from core.sprite_renderer import SpriteRenderer, Shape2DRenderer
        from core.camera_component import CameraComponent
        from core.physics_2d import BoxCollider2D, CircleCollider2D, Rigidbody2D
        from core.script_component import ScriptComponent
        from core.audio_source import AudioSource
        import core.primitives as prim3d
        import core.primitives_2d as prim2d

        name = type(comp).__name__

        def _remove():
            self._entity.remove_component(comp)
            self._rebuild()

        card = _Card(name, on_remove=_remove)
        bl = card.body_layout()

        # enabled checkbox in header area via body
        en_row = QHBoxLayout()
        en_cb = _check(comp.enabled, "Enabled", lambda v: setattr(comp, "enabled", v))
        en_row.addWidget(en_cb)
        en_row.addStretch()
        bl.addLayout(en_row)

        if isinstance(comp, MeshRenderer):
            import core.primitives as p3

            bl.addWidget(
                _FormRow(
                    "Shape",
                    _combo(
                        list(p3.PRIMITIVES),
                        comp.primitive,
                        lambda v: (comp.set_primitive(v), setattr(comp, "_vao", None)),
                    ),
                )
            )
            self._material_rows(bl, comp.material, comp)

        elif isinstance(comp, Shape2DRenderer):
            import core.primitives_2d as p2

            bl.addWidget(
                _FormRow(
                    "Shape", _combo(list(p2.PRIMITIVES_2D), comp.shape, comp.set_shape)
                )
            )
            w = _spin(
                0.01,
                9999,
                comp.size[0],
                on_change=lambda v: comp.set_size(v, comp.size[1]),
            )
            h = _spin(
                0.01,
                9999,
                comp.size[1],
                on_change=lambda v: comp.set_size(comp.size[0], v),
            )
            bl.addWidget(_FormRow("Width", w))
            bl.addWidget(_FormRow("Height", h))
            bl.addWidget(
                _FormRow(
                    "Color",
                    self._color_btn(
                        comp.color, lambda r, g, b, a: comp.set_color(r, g, b, a)
                    ),
                )
            )

        elif isinstance(comp, SpriteRenderer):
            import core.primitives_2d as p2

            bl.addWidget(
                _FormRow(
                    "Shape", _combo(list(p2.PRIMITIVES_2D), comp.shape, comp.set_shape)
                )
            )
            w = _spin(
                0.01,
                9999,
                comp.size[0],
                on_change=lambda v: comp.set_size(v, comp.size[1]),
            )
            h = _spin(
                0.01,
                9999,
                comp.size[1],
                on_change=lambda v: comp.set_size(comp.size[0], v),
            )
            bl.addWidget(_FormRow("Width", w))
            bl.addWidget(_FormRow("Height", h))
            self._material_rows(bl, comp.material, comp)
            fx = _check(
                comp.flip_x,
                "Flip X",
                lambda v: (setattr(comp, "flip_x", v), setattr(comp, "_vao", None)),
            )
            fy = _check(
                comp.flip_y,
                "Flip Y",
                lambda v: (setattr(comp, "flip_y", v), setattr(comp, "_vao", None)),
            )
            bl.addWidget(fx)
            bl.addWidget(fy)

        elif isinstance(comp, CameraComponent):
            bl.addWidget(
                _FormRow(
                    "Projection",
                    _combo(
                        ["perspective", "orthographic"],
                        comp.projection,
                        lambda v: setattr(comp, "projection", v),
                    ),
                )
            )
            bl.addWidget(
                _FormRow(
                    "FOV",
                    _spin(
                        10,
                        170,
                        comp.fov,
                        decimals=1,
                        on_change=lambda v: setattr(comp, "fov", v),
                    ),
                )
            )
            bl.addWidget(
                _FormRow(
                    "Near",
                    _spin(
                        0.001,
                        100,
                        comp.near,
                        decimals=3,
                        on_change=lambda v: setattr(comp, "near", v),
                    ),
                )
            )
            bl.addWidget(
                _FormRow(
                    "Far",
                    _spin(
                        1,
                        100000,
                        comp.far,
                        decimals=1,
                        on_change=lambda v: setattr(comp, "far", v),
                    ),
                )
            )
            bl.addWidget(
                _FormRow(
                    "Ortho Size",
                    _spin(
                        0.1,
                        9999,
                        comp.ortho_size,
                        decimals=2,
                        on_change=lambda v: setattr(comp, "ortho_size", v),
                    ),
                )
            )
            bl.addWidget(
                _check(
                    comp.is_main, "Main Camera", lambda v: setattr(comp, "is_main", v)
                )
            )

        elif isinstance(comp, BoxCollider2D):
            bl.addWidget(
                _FormRow(
                    "Width",
                    _spin(
                        0.01,
                        9999,
                        comp.width,
                        on_change=lambda v: setattr(comp, "width", v),
                    ),
                )
            )
            bl.addWidget(
                _FormRow(
                    "Height",
                    _spin(
                        0.01,
                        9999,
                        comp.height,
                        on_change=lambda v: setattr(comp, "height", v),
                    ),
                )
            )
            bl.addWidget(
                _check(
                    comp.is_trigger,
                    "Is Trigger",
                    lambda v: setattr(comp, "is_trigger", v),
                )
            )

        elif isinstance(comp, CircleCollider2D):
            bl.addWidget(
                _FormRow(
                    "Radius",
                    _spin(
                        0.001,
                        9999,
                        comp.radius,
                        on_change=lambda v: setattr(comp, "radius", v),
                    ),
                )
            )
            bl.addWidget(
                _check(
                    comp.is_trigger,
                    "Is Trigger",
                    lambda v: setattr(comp, "is_trigger", v),
                )
            )

        elif isinstance(comp, Rigidbody2D):
            bl.addWidget(
                _FormRow(
                    "Mass",
                    _spin(
                        0.001,
                        9999,
                        comp.mass,
                        on_change=lambda v: setattr(comp, "mass", v),
                    ),
                )
            )
            bl.addWidget(
                _FormRow(
                    "Gravity",
                    _spin(
                        -20,
                        20,
                        comp.gravity_scale,
                        step=0.1,
                        on_change=lambda v: setattr(comp, "gravity_scale", v),
                    ),
                )
            )
            bl.addWidget(
                _FormRow(
                    "Drag",
                    _spin(
                        0,
                        1,
                        comp.drag,
                        step=0.01,
                        on_change=lambda v: setattr(comp, "drag", v),
                    ),
                )
            )
            bl.addWidget(
                _check(
                    comp.is_kinematic,
                    "Kinematic",
                    lambda v: setattr(comp, "is_kinematic", v),
                )
            )

        elif isinstance(comp, AudioSource):
            bl.addWidget(
                _FormRow(
                    "Volume",
                    _spin(
                        0,
                        1,
                        comp.volume,
                        step=0.05,
                        on_change=lambda v: setattr(comp, "volume", v),
                    ),
                )
            )
            bl.addWidget(
                _FormRow(
                    "Pitch",
                    _spin(
                        0.1,
                        4,
                        comp.pitch,
                        step=0.1,
                        on_change=lambda v: setattr(comp, "pitch", v),
                    ),
                )
            )
            bl.addWidget(_check(comp.loop, "Loop", lambda v: setattr(comp, "loop", v)))
            bl.addWidget(
                _check(
                    comp.play_on_start,
                    "Play On Start",
                    lambda v: setattr(comp, "play_on_start", v),
                )
            )
            pr = QHBoxLayout()
            pb = QPushButton("▶ Play")
            pb.setFixedHeight(22)
            sb2 = QPushButton("⏹ Stop")
            sb2.setFixedHeight(22)
            pb.clicked.connect(lambda: comp.play() if comp.clip else None)
            sb2.clicked.connect(comp.stop)
            pr.addWidget(pb)
            pr.addWidget(sb2)
            bl.addLayout(pr)
            if comp.clip:
                bl.addWidget(QLabel(f"Clip: {comp.clip.name}"))

        elif isinstance(comp, ScriptComponent):
            path_lbl = QLabel(
                Path(comp.script_path).name if comp.script_path else "(none)"
            )
            path_lbl.setStyleSheet("color:#888; font-size:10px;")
            path_lbl.setWordWrap(True)
            bl.addWidget(_FormRow("File", path_lbl))

            btn_row = QHBoxLayout()
            browse_btn = QPushButton("Browse…")
            browse_btn.setFixedHeight(22)
            reload_btn = QPushButton("↺ Reload")
            reload_btn.setFixedHeight(22)
            edit_btn = QPushButton("✎ Edit")
            edit_btn.setFixedHeight(22)

            def _pick():
                p, _ = QFileDialog.getOpenFileName(
                    self,
                    "Select Script",
                    str(self.app.project.project_root or ""),
                    "Scripts (*.py *.amh);;All (*)",
                )
                if p:
                    comp.script_path = p
                    path_lbl.setText(Path(p).name)
                    comp.reload()

            browse_btn.clicked.connect(_pick)
            reload_btn.clicked.connect(lambda: comp.reload())

            def _edit():
                if comp.script_path:
                    mw = getattr(self.app, "main_window", None)
                    if mw and hasattr(mw, "script_editor"):
                        mw.script_editor.open_file(comp.script_path)
                        mw.script_editor.raise_()

            edit_btn.clicked.connect(_edit)

            btn_row.addWidget(browse_btn)
            btn_row.addWidget(reload_btn)
            btn_row.addWidget(edit_btn)
            bl.addLayout(btn_row)

            if comp._error:
                err_lbl = QLabel(comp._error.splitlines()[-1][:120])
                err_lbl.setStyleSheet(
                    "color:#f55; font-size:9px; background:#2a1414;"
                    "border-radius:3px; padding:3px;"
                )
                err_lbl.setWordWrap(True)
                bl.addWidget(err_lbl)
            elif comp._loaded:
                ok_lbl = QLabel("✓ Loaded")
                ok_lbl.setStyleSheet("color:#5f5; font-size:9px;")
                bl.addWidget(ok_lbl)

        self._vbox.addWidget(card)

    # ── Material rows ──────────────────────────────────────────────────────

    def _material_rows(self, bl: QVBoxLayout, mat, renderer=None):
        bl.addWidget(
            _FormRow(
                "Color",
                self._color_btn(
                    mat.color, lambda r, g, b, a: mat.set_color(r, g, b, a)
                ),
            )
        )
        bl.addWidget(
            _FormRow(
                "Ambient",
                _spin(
                    0,
                    1,
                    mat.ambient,
                    step=0.05,
                    on_change=lambda v: setattr(mat, "ambient", v),
                ),
            )
        )

        # Texture
        tex_name = (
            Path(mat._tex_path).name
            if getattr(mat, "_tex_path", "")
            else ("assigned" if mat.use_texture else "(none)")
        )
        tex_row = QHBoxLayout()
        tex_lbl = QLabel(tex_name)
        tex_lbl.setStyleSheet("color:#888; font-size:10px;")
        tex_row.addWidget(tex_lbl, 1)

        assign_btn = QPushButton("Assign…")
        assign_btn.setFixedHeight(20)
        assign_btn.setStyleSheet("QPushButton{font-size:10px;padding:1px 6px;}")

        def _assign():
            p, _ = QFileDialog.getOpenFileName(
                self,
                "Select Texture",
                str(self.app.project.project_root or ""),
                "Images (*.png *.jpg *.jpeg *.bmp *.tga);;All (*)",
            )
            if not p:
                return
            ctx = getattr(self.app.main_window.viewport, "ctx", None)
            if ctx is None:
                self.app.console.warning("GL context not ready.")
                return
            ok = mat.upload_texture_from_path(ctx, p)
            if ok:
                tex_lbl.setText(Path(p).name)
                if renderer:
                    setattr(renderer, "_vao", None)
                self.app.console.info(f"Texture '{Path(p).name}' assigned.")

        assign_btn.clicked.connect(_assign)
        tex_row.addWidget(assign_btn)

        if mat.use_texture:
            clr_btn = QPushButton("✕")
            clr_btn.setFixedSize(20, 20)
            clr_btn.setStyleSheet(
                "QPushButton{color:#f55;border:none;background:transparent;}"
            )

            def _clear():
                mat.texture = None
                mat.use_texture = False
                if hasattr(mat, "_tex_path"):
                    mat._tex_path = ""
                tex_lbl.setText("(none)")
                if renderer:
                    setattr(renderer, "_vao", None)

            clr_btn.clicked.connect(_clear)
            tex_row.addWidget(clr_btn)

        tex_w = QWidget()
        tex_w.setLayout(tex_row)
        bl.addWidget(_FormRow("Texture", tex_w))

    # ── Color picker ───────────────────────────────────────────────────────

    def _color_btn(self, arr, on_change):
        c = arr
        hex_col = f"#{int(c[0]*255):02x}{int(c[1]*255):02x}{int(c[2]*255):02x}"
        btn = QPushButton()
        btn.setFixedSize(52, 20)
        btn.setStyleSheet(
            f"background:{hex_col}; border:1px solid #555; border-radius:3px;"
        )

        def _pick():
            from PySide6.QtWidgets import QColorDialog

            dlg = QColorDialog()
            if dlg.exec():
                q = dlg.selectedColor()
                on_change(q.redF(), q.greenF(), q.blueF(), q.alphaF())
                btn.setStyleSheet(
                    f"background:{q.name()}; border:1px solid #555; border-radius:3px;"
                )

        btn.clicked.connect(_pick)
        return btn

    # ── Add component button ───────────────────────────────────────────────

    def _build_add_button(self):
        btn = QPushButton("＋  Add Component")
        btn.setFixedHeight(30)
        btn.setStyleSheet(
            "QPushButton{background:#1e3a1e;border:1px solid #2e6b2e;"
            "border-radius:5px;color:#5f5;font-size:11px;}"
            "QPushButton:hover{background:#254a25;}"
        )
        btn.clicked.connect(self._on_add)
        self._vbox.addWidget(btn)

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
            "AudioSource",
        ]
        choice, ok = QInputDialog.getItem(
            self, "Add Component", "Component:", opts, 0, False
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
