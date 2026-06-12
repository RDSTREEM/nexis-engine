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

from ui.theme import (
    BG_SURFACE,
    BG_RAISED,
    BG_INPUT,
    BG_CARD_HDR,
    ACCENT,
    ACCENT_DIM,
    BORDER,
    BORDER_LIGHT,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
    GREEN,
    GREEN_BG,
    GREEN_BORDER,
    RED,
    RED_BG,
    PANEL_TOOLBAR_H,
    CARD_HEADER_H,
    FORM_LABEL_W,
)


class _Card(QWidget):
    def __init__(self, title: str, on_remove=None, parent=None):
        super().__init__(parent)
        self._collapsed = False
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header
        header = QWidget()
        header.setFixedHeight(CARD_HEADER_H)
        header.setStyleSheet(
            f"background: {BG_CARD_HDR}; border-radius: 5px 5px 0 0;"
            f"border: 1px solid {BORDER}; border-bottom: none;"
        )
        hrow = QHBoxLayout(header)
        hrow.setContentsMargins(8, 0, 6, 0)
        hrow.setSpacing(4)

        self._arrow = QLabel("▾")
        self._arrow.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px;")
        self._arrow.setFixedWidth(14)
        hrow.addWidget(self._arrow)

        self._title_lbl = QLabel(title)
        self._title_lbl.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-weight: 600; font-size: 11px; letter-spacing: 0.3px;"
        )
        hrow.addWidget(self._title_lbl, 1)

        if on_remove:
            rm = QPushButton("✕")
            rm.setFixedSize(18, 18)
            rm.setStyleSheet(
                f"QPushButton{{color:{TEXT_MUTED};border:none;background:transparent;font-size:11px;}}"
                f"QPushButton:hover{{color:{RED};}}"
            )
            rm.clicked.connect(on_remove)
            hrow.addWidget(rm)

        header.mousePressEvent = lambda _e: self._toggle()
        outer.addWidget(header)

        # Body
        self._body = QWidget()
        self._body.setStyleSheet(
            f"background: {BG_RAISED}; border: 1px solid {BORDER};"
            f"border-top: none; border-radius: 0 0 5px 5px;"
        )
        outer.addWidget(self._body)

    def body_layout(self) -> QVBoxLayout:
        if not self._body.layout():
            lay = QVBoxLayout(self._body)
            lay.setContentsMargins(10, 8, 10, 10)
            lay.setSpacing(5)
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
        lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        lbl.setFixedWidth(FORM_LABEL_W)
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
        f"QDoubleSpinBox{{background:{BG_INPUT};border:1px solid {BORDER_LIGHT};"
        f"border-radius:4px;padding:2px 5px;color:{TEXT_PRIMARY};font-size:11px;}}"
        f"QDoubleSpinBox:focus{{border-color:{ACCENT};}}"
    )
    if on_change:
        sb.valueChanged.connect(on_change)
    return sb


def _check(val: bool, label: str = "", on_change=None):
    cb = QCheckBox(label)
    cb.setChecked(val)
    cb.setStyleSheet(f"QCheckBox{{color:{TEXT_SECONDARY};font-size:11px;}}")
    if on_change:
        cb.toggled.connect(on_change)
    return cb


def _combo(items: list, current: str, on_change=None):
    c = QComboBox()
    c.addItems(items)
    c.setCurrentText(current)
    c.setStyleSheet(
        f"QComboBox{{background:{BG_INPUT};border:1px solid {BORDER_LIGHT};"
        f"border-radius:4px;padding:2px 5px;color:{TEXT_PRIMARY};font-size:11px;}}"
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
        row.setSpacing(3)
        labels = ["X", "Y", "Z"]
        colors = ["#c04444", "#44aa44", "#4477cc"]
        for i in range(3):
            lbl = QLabel(labels[i])
            lbl.setStyleSheet(f"color: {colors[i]}; font-size: 10px; font-weight: 600;")
            lbl.setFixedWidth(12)
            sb = QDoubleSpinBox()
            sb.setRange(-99999, 99999)
            sb.setDecimals(3)
            sb.setSingleStep(0.1)
            sb.setValue(float(arr[i]))
            sb.setStyleSheet(
                f"QDoubleSpinBox{{background:{BG_INPUT};border:1px solid {BORDER_LIGHT};"
                f"border-radius:4px;padding:2px 4px;color:{TEXT_PRIMARY};font-size:11px;}}"
                f"QDoubleSpinBox:focus{{border-color:{ACCENT};}}"
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

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(
            f"QScrollArea{{border:none;background:{BG_SURFACE};}}"
        )

        self._root = QWidget()
        self._root.setStyleSheet(f"background: {BG_SURFACE};")
        self._vbox = QVBoxLayout(self._root)
        self._vbox.setContentsMargins(6, 6, 6, 6)
        self._vbox.setSpacing(5)
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
        lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; padding: 30px;")
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
        card.setStyleSheet(
            f"background: {BG_RAISED}; border-radius: 5px; border: 1px solid {BORDER};"
        )
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
            f"QLineEdit{{background:{BG_INPUT};border:1px solid {BORDER_LIGHT};"
            f"border-radius:4px;color:{TEXT_PRIMARY};font-size:12px;font-weight:600;"
            f"padding:4px 8px;}}"
            f"QLineEdit:focus{{border-color:{ACCENT};}}"
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

        tag_count = len(e.tags)
        tag_label = f"Tags ({tag_count})" if tag_count else "Tags"
        tag_btn = QPushButton(tag_label)
        tag_btn.setFixedHeight(24)
        tag_btn.setStyleSheet(
            f"QPushButton{{background:{BG_INPUT};border:1px solid {BORDER_LIGHT};"
            f"color:{TEXT_MUTED};font-size:10px;border-radius:4px;padding:2px 8px;}}"
            f"QPushButton:hover{{border-color:{ACCENT};color:{TEXT_SECONDARY};}}"
        )

        def _edit_tags():
            from ui.panels.tag_selector import TagSelectorDialog

            dlg = TagSelectorDialog(e.tags, self.app.project, self)
            if dlg.exec():
                e.tags = dlg.selected_tags
                c = len(e.tags)
                tag_btn.setText(f"Tags ({c})" if c else "Tags")

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

        name = type(comp).__name__

        def _remove():
            self._entity.remove_component(comp)
            self._rebuild()

        card = _Card(name, on_remove=_remove)
        bl = card.body_layout()

        # Enabled toggle
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
            bl.addWidget(
                _FormRow(
                    "Width",
                    _spin(
                        0.01,
                        9999,
                        comp.size[0],
                        on_change=lambda v: comp.set_size(v, comp.size[1]),
                    ),
                )
            )
            bl.addWidget(
                _FormRow(
                    "Height",
                    _spin(
                        0.01,
                        9999,
                        comp.size[1],
                        on_change=lambda v: comp.set_size(comp.size[0], v),
                    ),
                )
            )
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
            bl.addWidget(
                _FormRow(
                    "Width",
                    _spin(
                        0.01,
                        9999,
                        comp.size[0],
                        on_change=lambda v: comp.set_size(v, comp.size[1]),
                    ),
                )
            )
            bl.addWidget(
                _FormRow(
                    "Height",
                    _spin(
                        0.01,
                        9999,
                        comp.size[1],
                        on_change=lambda v: comp.set_size(comp.size[0], v),
                    ),
                )
            )
            self._material_rows(bl, comp.material, comp)
            bl.addWidget(
                _check(
                    comp.flip_x,
                    "Flip X",
                    lambda v: (setattr(comp, "flip_x", v), setattr(comp, "_vao", None)),
                )
            )
            bl.addWidget(
                _check(
                    comp.flip_y,
                    "Flip Y",
                    lambda v: (setattr(comp, "flip_y", v), setattr(comp, "_vao", None)),
                )
            )

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
            pb.setFixedHeight(24)
            sb2 = QPushButton("⏹ Stop")
            sb2.setFixedHeight(24)
            pb.clicked.connect(lambda: comp.play() if comp.clip else None)
            sb2.clicked.connect(comp.stop)
            pr.addWidget(pb)
            pr.addWidget(sb2)
            bl.addLayout(pr)
            if comp.clip:
                clip_lbl = QLabel(f"Clip: {comp.clip.name}")
                clip_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
                bl.addWidget(clip_lbl)

        elif isinstance(comp, ScriptComponent):
            path_lbl = QLabel(
                Path(comp.script_path).name if comp.script_path else "(none)"
            )
            path_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
            path_lbl.setWordWrap(True)
            bl.addWidget(_FormRow("File", path_lbl))

            btn_row = QHBoxLayout()
            browse_btn = QPushButton("Browse…")
            reload_btn = QPushButton("↺ Reload")
            edit_btn = QPushButton("✎ Edit")
            for b in (browse_btn, reload_btn, edit_btn):
                b.setFixedHeight(24)
            btn_row.addWidget(browse_btn)
            btn_row.addWidget(reload_btn)
            btn_row.addWidget(edit_btn)
            bl.addLayout(btn_row)

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

            if comp._error:
                err_lbl = QLabel(comp._error.splitlines()[-1][:120])
                err_lbl.setStyleSheet(
                    f"color: {RED}; font-size: 10px; background: {RED_BG};"
                    "border-radius: 3px; padding: 3px;"
                )
                err_lbl.setWordWrap(True)
                bl.addWidget(err_lbl)
            elif comp._loaded:
                ok_lbl = QLabel("✓ Loaded")
                ok_lbl.setStyleSheet(f"color: {GREEN}; font-size: 10px;")
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

        tex_name = (
            Path(mat._tex_path).name
            if getattr(mat, "_tex_path", "")
            else ("assigned" if mat.use_texture else "(none)")
        )
        tex_row = QHBoxLayout()
        tex_lbl = QLabel(tex_name)
        tex_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        tex_row.addWidget(tex_lbl, 1)

        assign_btn = QPushButton("Assign…")
        assign_btn.setFixedHeight(22)
        assign_btn.setStyleSheet(
            f"QPushButton{{font-size:11px;padding:1px 8px;background:{BG_INPUT};"
            f"border:1px solid {BORDER_LIGHT};border-radius:4px;color:{TEXT_SECONDARY};}}"
            f"QPushButton:hover{{border-color:{ACCENT};}}"
        )

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
            clr_btn.setFixedSize(22, 22)
            clr_btn.setStyleSheet(
                f"QPushButton{{color:{RED};border:none;background:transparent;font-size:12px;}}"
                f"QPushButton:hover{{color:#ff4444;}}"
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
        btn.setFixedSize(52, 22)
        btn.setStyleSheet(
            f"background:{hex_col}; border:1px solid {BORDER_LIGHT}; border-radius:4px;"
        )

        def _pick():
            dlg = QColorDialog()
            if dlg.exec():
                q = dlg.selectedColor()
                on_change(q.redF(), q.greenF(), q.blueF(), q.alphaF())
                btn.setStyleSheet(
                    f"background:{q.name()}; border:1px solid {BORDER_LIGHT}; border-radius:4px;"
                )

        btn.clicked.connect(_pick)
        return btn

    # ── Add component button ───────────────────────────────────────────────

    def _build_add_button(self):
        btn = QPushButton("＋  Add Component")
        btn.setFixedHeight(32)
        btn.setStyleSheet(
            f"QPushButton{{background:{GREEN_BG};border:1px solid {GREEN_BORDER};"
            f"border-radius:5px;color:{GREEN};font-size:12px;}}"
            f"QPushButton:hover{{background:#1f3828;}}"
            f"QPushButton:pressed{{background:#141f18;}}"
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
