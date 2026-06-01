from __future__ import annotations

from pathlib import Path

import numpy as np
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QColor, QFont
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDockWidget,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QStackedWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
    QDoubleSpinBox,
    QSpinBox,
    QCheckBox,
    QComboBox,
    QColorDialog,
)

from ui.start_screen import CreateProjectDialog, StartScreen
from ui.viewport import ViewportWidget

# ============================================================
# Helpers
# ============================================================


def _hline() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.HLine)
    f.setFrameShadow(QFrame.Sunken)
    return f


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet("font-weight: bold; font-size: 11px; color: #aaaaaa;")
    return lbl


# ============================================================
# Vec3 editor widget (used for position / rotation / scale)
# ============================================================


class Vec3Widget(QWidget):
    def __init__(self, label: str, value: np.ndarray, callback, parent=None):
        super().__init__(parent)
        self._cb = callback
        self._val = value
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
            idx = i
            sb.valueChanged.connect(lambda v, idx=idx: self._on_change(idx, v))
            row.addWidget(sb)
            self._spins.append(sb)

    def _on_change(self, idx: int, val: float):
        self._val[idx] = val
        self._cb()

    def set_values(self, value: np.ndarray):
        for i, sb in enumerate(self._spins):
            sb.blockSignals(True)
            sb.setValue(float(value[i]))
            sb.blockSignals(False)


# ============================================================
# Inspector panel
# ============================================================


class InspectorPanel(QWidget):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self._entity = None
        self._vec3_widgets: dict = {}

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._content = QWidget()
        self._layout = QVBoxLayout(self._content)
        self._layout.setAlignment(Qt.AlignTop)
        self._layout.setSpacing(4)
        scroll.setWidget(self._content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        self._show_empty()

    # ------------------------------------------------------------------

    def show_entity(self, entity) -> None:
        self._entity = entity
        self._rebuild()

    def clear(self) -> None:
        self._entity = None
        self._rebuild()

    # ------------------------------------------------------------------

    def _clear_layout(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._vec3_widgets.clear()

    def _show_empty(self):
        self._clear_layout()
        lbl = QLabel("Select an entity to inspect.")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("color: #666666;")
        self._layout.addWidget(lbl)

    def _rebuild(self):
        if self._entity is None:
            self._show_empty()
            return
        self._clear_layout()
        self._build_entity_header()
        self._build_transform()
        for comp in self._entity.components:
            from core.transform import Transform

            if isinstance(comp, Transform):
                continue
            self._build_component(comp)
        self._build_add_component_button()

    # --- entity header ---

    def _build_entity_header(self):
        e = self._entity
        row = QHBoxLayout()
        enabled_cb = QCheckBox()
        enabled_cb.setChecked(e.enabled)
        enabled_cb.toggled.connect(lambda v: setattr(e, "enabled", v))
        row.addWidget(enabled_cb)

        name_edit = QLineEdit(e.name)
        name_edit.textChanged.connect(
            lambda v: setattr(e, "name", v) or self.app.main_window.refresh_hierarchy()
        )
        row.addWidget(name_edit)
        self._layout.addLayout(row)
        self._layout.addWidget(_hline())

    # --- transform ---

    def _build_transform(self):
        t = self._entity.transform
        self._layout.addWidget(_section_label("Transform"))

        def _dirty():
            t._dirty = True

        pos_w = Vec3Widget("Position", t.position, _dirty)
        rot_w = Vec3Widget("Rotation", t.rotation, _dirty)
        scl_w = Vec3Widget("Scale", t.scale, _dirty)
        self._layout.addWidget(pos_w)
        self._layout.addWidget(rot_w)
        self._layout.addWidget(scl_w)
        self._vec3_widgets["transform"] = (pos_w, rot_w, scl_w)
        self._layout.addWidget(_hline())

    # --- generic component ---

    def _build_component(self, comp) -> None:
        from core.mesh_renderer import MeshRenderer
        from core.sprite_renderer import SpriteRenderer
        from core.camera_component import CameraComponent

        header_row = QHBoxLayout()
        cb = QCheckBox()
        cb.setChecked(comp.enabled)
        cb.toggled.connect(lambda v: setattr(comp, "enabled", v))
        header_row.addWidget(cb)
        header_row.addWidget(_section_label(type(comp).__name__))
        header_row.addStretch()
        rem_btn = QPushButton("✕")
        rem_btn.setFixedSize(20, 20)
        rem_btn.setStyleSheet("color: #ff5555; border: none;")
        rem_btn.clicked.connect(lambda: self._remove_component(comp))
        header_row.addWidget(rem_btn)
        self._layout.addLayout(header_row)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)

        if isinstance(comp, MeshRenderer):
            prim_combo = QComboBox()
            prim_combo.addItems(["cube", "quad"])
            prim_combo.setCurrentText(comp.primitive)
            prim_combo.currentTextChanged.connect(lambda v: comp.set_primitive(v))
            form.addRow("Primitive", prim_combo)
            self._add_material_rows(form, comp.material)

        elif isinstance(comp, SpriteRenderer):
            self._add_material_rows(form, comp.material)
            w_spin = QDoubleSpinBox()
            w_spin.setRange(0.01, 9999)
            w_spin.setValue(float(comp.size[0]))
            h_spin = QDoubleSpinBox()
            h_spin.setRange(0.01, 9999)
            h_spin.setValue(float(comp.size[1]))
            w_spin.valueChanged.connect(lambda v: comp.set_size(v, comp.size[1]))
            h_spin.valueChanged.connect(lambda v: comp.set_size(comp.size[0], v))
            form.addRow("Width", w_spin)
            form.addRow("Height", h_spin)

        elif isinstance(comp, CameraComponent):
            proj_combo = QComboBox()
            proj_combo.addItems(["perspective", "orthographic"])
            proj_combo.setCurrentText(comp.projection)
            proj_combo.currentTextChanged.connect(
                lambda v: setattr(comp, "projection", v)
            )
            form.addRow("Projection", proj_combo)

            fov_spin = QDoubleSpinBox()
            fov_spin.setRange(10, 170)
            fov_spin.setValue(comp.fov)
            fov_spin.valueChanged.connect(lambda v: setattr(comp, "fov", v))
            form.addRow("FOV", fov_spin)

            near_spin = QDoubleSpinBox()
            near_spin.setRange(0.001, 100)
            near_spin.setValue(comp.near)
            near_spin.setDecimals(3)
            near_spin.valueChanged.connect(lambda v: setattr(comp, "near", v))
            form.addRow("Near", near_spin)

            far_spin = QDoubleSpinBox()
            far_spin.setRange(1, 100000)
            far_spin.setValue(comp.far)
            far_spin.valueChanged.connect(lambda v: setattr(comp, "far", v))
            form.addRow("Far", far_spin)

            main_cb = QCheckBox()
            main_cb.setChecked(comp.is_main)
            main_cb.toggled.connect(lambda v: setattr(comp, "is_main", v))
            form.addRow("Main Camera", main_cb)

        self._layout.addLayout(form)
        self._layout.addWidget(_hline())

    def _add_material_rows(self, form: QFormLayout, mat) -> None:
        color_btn = QPushButton()
        c = mat.color
        color_btn.setStyleSheet(
            f"background-color: rgb({int(c[0]*255)},{int(c[1]*255)},{int(c[2]*255)});"
        )

        def _pick_color():
            dlg = QColorDialog()
            if dlg.exec():
                qc = dlg.selectedColor()
                mat.set_color(qc.redF(), qc.greenF(), qc.blueF(), qc.alphaF())
                color_btn.setStyleSheet(
                    f"background-color: rgb({qc.red()},{qc.green()},{qc.blue()});"
                )

        color_btn.clicked.connect(_pick_color)
        form.addRow("Color", color_btn)

        amb_spin = QDoubleSpinBox()
        amb_spin.setRange(0, 1)
        amb_spin.setSingleStep(0.05)
        amb_spin.setValue(mat.ambient)
        amb_spin.valueChanged.connect(lambda v: setattr(mat, "ambient", v))
        form.addRow("Ambient", amb_spin)

    def _remove_component(self, comp) -> None:
        if self._entity:
            self._entity.remove_component(comp)
            self._rebuild()

    def _build_add_component_button(self) -> None:
        btn = QPushButton("+ Add Component")
        btn.clicked.connect(self._on_add_component)
        self._layout.addWidget(btn)

    def _on_add_component(self) -> None:
        if self._entity is None:
            return
        options = ["MeshRenderer", "SpriteRenderer", "CameraComponent"]
        choice, ok = QInputDialog.getItem(
            self, "Add Component", "Select component type:", options, 0, False
        )
        if not ok:
            return
        from core.mesh_renderer import MeshRenderer
        from core.sprite_renderer import SpriteRenderer
        from core.camera_component import CameraComponent

        mapping = {
            "MeshRenderer": MeshRenderer,
            "SpriteRenderer": SpriteRenderer,
            "CameraComponent": CameraComponent,
        }
        cls = mapping.get(choice)
        if cls:
            self._entity.add_component(cls())
            self._rebuild()


# ============================================================
# Main Window
# ============================================================


class MainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setWindowTitle("NEXIS")
        self.resize(1440, 900)
        self.setStyleSheet(_DARK_STYLE)
        self._create_menu()
        self._create_docks()
        self._create_central_area()
        self._create_console_output()
        self.app.console.set_ui_widget(self.console_text_edit)
        self.show_start_screen()

    # ------------------------------------------------------------------
    # Menu
    # ------------------------------------------------------------------

    def _create_menu(self) -> None:
        # File
        file_menu = self.menuBar().addMenu("File")

        new_act = QAction("New Project…", self)
        new_act.setShortcut("Ctrl+Shift+N")
        new_act.triggered.connect(self.on_request_create_project)
        file_menu.addAction(new_act)

        open_act = QAction("Open Project…", self)
        open_act.setShortcut("Ctrl+O")
        open_act.triggered.connect(self._on_request_open_project)
        file_menu.addAction(open_act)

        self.save_act = QAction("Save", self)
        self.save_act.setShortcut("Ctrl+S")
        self.save_act.setEnabled(False)
        self.save_act.triggered.connect(self.app.save_project)
        file_menu.addAction(self.save_act)

        file_menu.addSeparator()

        self.close_project_action = QAction("Close Project", self)
        self.close_project_action.setEnabled(False)
        self.close_project_action.triggered.connect(self.app.close_project)
        file_menu.addAction(self.close_project_action)

        # Edit
        edit_menu = self.menuBar().addMenu("Edit")
        add_entity_act = QAction("Add Entity", self)
        add_entity_act.setShortcut("Ctrl+Shift+A")
        add_entity_act.triggered.connect(self._on_add_entity)
        edit_menu.addAction(add_entity_act)

        del_entity_act = QAction("Delete Entity", self)
        del_entity_act.setShortcut("Delete")
        del_entity_act.triggered.connect(self._on_delete_entity)
        edit_menu.addAction(del_entity_act)

    # ------------------------------------------------------------------
    # Docks
    # ------------------------------------------------------------------

    def _create_docks(self) -> None:
        # --- Scene Hierarchy ---
        hier_container = QWidget()
        hier_layout = QVBoxLayout(hier_container)
        hier_layout.setContentsMargins(4, 4, 4, 4)
        hier_layout.setSpacing(4)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("+ Entity")
        add_btn.clicked.connect(self._on_add_entity)
        del_btn = QPushButton("✕")
        del_btn.setFixedWidth(28)
        del_btn.clicked.connect(self._on_delete_entity)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(del_btn)
        hier_layout.addLayout(btn_row)

        self.scene_hierarchy = QTreeWidget()
        self.scene_hierarchy.setHeaderLabel("Scene")
        self.scene_hierarchy.setContextMenuPolicy(Qt.CustomContextMenu)
        self.scene_hierarchy.customContextMenuRequested.connect(
            self._on_hierarchy_context_menu
        )
        self.scene_hierarchy.itemClicked.connect(self._on_hierarchy_item_clicked)
        hier_layout.addWidget(self.scene_hierarchy)

        self.scene_dock = QDockWidget("Scene Hierarchy", self)
        self.scene_dock.setWidget(hier_container)
        self.scene_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.scene_dock)

        # --- Inspector ---
        self.inspector_panel = InspectorPanel(self.app)
        self.inspector_dock = QDockWidget("Inspector", self)
        self.inspector_dock.setWidget(self.inspector_panel)
        self.inspector_dock.setAllowedAreas(
            Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea
        )
        self.addDockWidget(Qt.RightDockWidgetArea, self.inspector_dock)

    # ------------------------------------------------------------------
    # Central area (start screen + viewport)
    # ------------------------------------------------------------------

    def _create_central_area(self) -> None:
        self.stacked_central = QStackedWidget()

        self.start_screen = StartScreen(
            self.app.console,
            self.on_request_create_project,
            self._on_request_open_project,
            self._on_request_open_recent_project,
        )

        # viewport wrapper with toolbar
        vp_container = QWidget()
        vp_layout = QVBoxLayout(vp_container)
        vp_layout.setContentsMargins(0, 0, 0, 0)
        vp_layout.setSpacing(0)

        self._toolbar = self._build_viewport_toolbar()
        vp_layout.addWidget(self._toolbar)

        self.viewport_widget = ViewportWidget(self.app)
        vp_layout.addWidget(self.viewport_widget)

        self.stacked_central.addWidget(self.start_screen)
        self.stacked_central.addWidget(vp_container)
        self.setCentralWidget(self.stacked_central)

    def _build_viewport_toolbar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(32)
        bar.setStyleSheet("background: #1e1e1e; border-bottom: 1px solid #333;")
        row = QHBoxLayout(bar)
        row.setContentsMargins(8, 0, 8, 0)
        row.setSpacing(6)

        # 2D / 3D toggle — only shown for 3D projects
        self._cam_mode_btn = QPushButton("3D")
        self._cam_mode_btn.setFixedWidth(40)
        self._cam_mode_btn.setCheckable(True)
        self._cam_mode_btn.setToolTip(
            "Toggle editor camera between 3D (perspective) and 2D (orthographic)"
        )
        self._cam_mode_btn.clicked.connect(self._on_toggle_cam_mode)
        row.addWidget(self._cam_mode_btn)

        row.addWidget(_vline())

        # play / pause / stop placeholders (wired up in Phase 6)
        self._play_btn = QPushButton("▶")
        self._pause_btn = QPushButton("⏸")
        self._stop_btn = QPushButton("⏹")
        for btn in (self._play_btn, self._pause_btn, self._stop_btn):
            btn.setFixedWidth(32)
            btn.setEnabled(False)  # enabled in Phase 6
            row.addWidget(btn)

        row.addStretch()

        # scene label
        self._scene_label = QLabel("")
        self._scene_label.setStyleSheet("color: #888888; font-size: 11px;")
        row.addWidget(self._scene_label)

        return bar

    # ------------------------------------------------------------------
    # Console
    # ------------------------------------------------------------------

    def _create_console_output(self) -> None:
        self.console_text_edit = QTextEdit()
        self.console_text_edit.setReadOnly(True)
        self.console_text_edit.setMinimumHeight(140)
        self.console_text_edit.setFont(QFont("Consolas", 9))

        clear_btn = QPushButton("Clear")
        clear_btn.setFixedHeight(22)
        clear_btn.clicked.connect(self.console_text_edit.clear)

        wrapper = QWidget()
        wl = QVBoxLayout(wrapper)
        wl.setContentsMargins(0, 0, 0, 0)
        wl.setSpacing(0)
        wl.addWidget(clear_btn)
        wl.addWidget(self.console_text_edit)

        self.console_dock = QDockWidget("Console", self)
        self.console_dock.setWidget(wrapper)
        self.console_dock.setAllowedAreas(Qt.BottomDockWidgetArea)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.console_dock)

    # ------------------------------------------------------------------
    # Show / hide
    # ------------------------------------------------------------------

    def _set_editor_mode(self, enabled: bool) -> None:
        self.scene_dock.setVisible(enabled)
        self.inspector_dock.setVisible(enabled)
        self.console_dock.setVisible(enabled)
        self.close_project_action.setEnabled(enabled)
        self.save_act.setEnabled(enabled)

    def show_start_screen(self) -> None:
        self._set_editor_mode(False)
        self.stacked_central.setCurrentWidget(self.start_screen)
        self.start_screen.reload_recent()
        self.setWindowTitle("NEXIS")

    def show_viewport(self) -> None:
        self._set_editor_mode(True)
        self.stacked_central.setCurrentIndex(1)
        self.setWindowTitle(f"NEXIS — {self.app.project.project_name}")

    # ------------------------------------------------------------------
    # Project loaded
    # ------------------------------------------------------------------

    def on_project_loaded(self) -> None:
        pt = self.app.project.project_type  # "2D" or "3D"

        # camera mode
        if pt == "2D":
            self.viewport_widget.camera.set_mode("2d")
            self._cam_mode_btn.setVisible(False)  # no toggle in 2D projects
        else:
            self.viewport_widget.camera.set_mode("3d")
            self._cam_mode_btn.setVisible(True)
            self._cam_mode_btn.setChecked(False)
            self._cam_mode_btn.setText("3D")

        self._scene_label.setText(
            self.app.project.active_scene.name if self.app.project.active_scene else ""
        )
        self.refresh_hierarchy()
        self.show_viewport()
        self.app.console.info(f"Project loaded: {self.app.project.project_name} ({pt})")

    # ------------------------------------------------------------------
    # Camera toggle
    # ------------------------------------------------------------------

    def _on_toggle_cam_mode(self) -> None:
        cam = self.viewport_widget.camera
        if cam.mode == "3d":
            cam.set_mode("2d")
            self._cam_mode_btn.setText("2D")
        else:
            cam.set_mode("3d")
            self._cam_mode_btn.setText("3D")

    # ------------------------------------------------------------------
    # Scene hierarchy
    # ------------------------------------------------------------------

    def refresh_hierarchy(self) -> None:
        self.scene_hierarchy.clear()
        scene = self.app.active_scene
        if scene is None:
            return
        root = QTreeWidgetItem([scene.name])
        root.setData(0, Qt.UserRole, None)
        self.scene_hierarchy.addTopLevelItem(root)
        for entity in scene.entities:
            item = QTreeWidgetItem([entity.name])
            item.setData(0, Qt.UserRole, entity.id)
            root.addChild(item)
        root.setExpanded(True)

    def _on_hierarchy_item_clicked(self, item: QTreeWidgetItem, _col: int) -> None:
        entity_id = item.data(0, Qt.UserRole)
        if entity_id is None:
            self.inspector_panel.clear()
            return
        scene = self.app.active_scene
        if scene:
            entity = scene.get_entity_by_id(entity_id)
            if entity:
                self.inspector_panel.show_entity(entity)

    def _on_hierarchy_context_menu(self, pos) -> None:
        menu = QMenu()
        menu.addAction("Add Entity", self._on_add_entity)
        menu.addAction("Delete Entity", self._on_delete_entity)
        menu.addAction("Rename", self._on_rename_entity)
        menu.exec(self.scene_hierarchy.mapToGlobal(pos))

    # ------------------------------------------------------------------
    # Entity operations
    # ------------------------------------------------------------------

    def _on_add_entity(self) -> None:
        scene = self.app.active_scene
        if scene is None:
            return
        name, ok = QInputDialog.getText(
            self, "New Entity", "Entity name:", text="Entity"
        )
        if ok and name.strip():
            scene.create_entity(name.strip())
            self.refresh_hierarchy()

    def _on_delete_entity(self) -> None:
        scene = self.app.active_scene
        if scene is None:
            return
        item = self.scene_hierarchy.currentItem()
        if item is None:
            return
        entity_id = item.data(0, Qt.UserRole)
        if entity_id is None:
            return
        entity = scene.get_entity_by_id(entity_id)
        if entity is None:
            return
        reply = QMessageBox.question(
            self,
            "Delete Entity",
            f"Delete '{entity.name}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            scene.remove_entity(entity)
            self.inspector_panel.clear()
            self.refresh_hierarchy()

    def _on_rename_entity(self) -> None:
        item = self.scene_hierarchy.currentItem()
        if item is None:
            return
        entity_id = item.data(0, Qt.UserRole)
        if entity_id is None:
            return
        scene = self.app.active_scene
        entity = scene.get_entity_by_id(entity_id) if scene else None
        if entity is None:
            return
        name, ok = QInputDialog.getText(
            self, "Rename Entity", "New name:", text=entity.name
        )
        if ok and name.strip():
            entity.name = name.strip()
            self.refresh_hierarchy()

    # ------------------------------------------------------------------
    # Project dialogs
    # ------------------------------------------------------------------

    def on_request_create_project(self) -> None:
        dlg = CreateProjectDialog(self)
        if dlg.exec() == QDialog.Accepted:
            folder, name, ptype = dlg.result_data()
            if folder and name:
                self.app.create_project(Path(folder), name, ptype)

    def _on_request_open_project(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open NEXIS Project",
            str(Path.home()),
            "NEXIS Project (*.nexis);;All Files (*)",
        )
        if path:
            self.app.open_project(path)

    def _on_request_open_recent_project(self, path: str) -> None:
        self.app.open_project(path)


# ============================================================
# Small helper widget for toolbar separator
# ============================================================


def _vline() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.VLine)
    f.setFrameShadow(QFrame.Sunken)
    return f


# ============================================================
# Dark stylesheet
# ============================================================

_DARK_STYLE = """
QMainWindow, QWidget {
    background-color: #2b2b2b;
    color: #dddddd;
}
QMenuBar {
    background-color: #1e1e1e;
    color: #cccccc;
}
QMenuBar::item:selected { background: #3c3c3c; }
QMenu { background: #2b2b2b; border: 1px solid #444; }
QMenu::item:selected { background: #3c8dde; }
QDockWidget::title {
    background: #1e1e1e;
    padding: 4px;
    font-size: 11px;
    color: #aaaaaa;
}
QTreeWidget {
    background: #252525;
    border: none;
    color: #dddddd;
}
QTreeWidget::item:selected { background: #3c8dde; color: white; }
QTextEdit {
    background: #1a1a1a;
    color: #cccccc;
    border: none;
    font-family: Consolas, monospace;
}
QPushButton {
    background: #3c3c3c;
    border: 1px solid #555;
    border-radius: 3px;
    padding: 3px 8px;
    color: #dddddd;
}
QPushButton:hover  { background: #4a4a4a; }
QPushButton:pressed { background: #2a2a2a; }
QPushButton:checked { background: #3c8dde; color: white; }
QPushButton:disabled { color: #555555; }
QDoubleSpinBox, QSpinBox, QLineEdit, QComboBox {
    background: #1e1e1e;
    border: 1px solid #444;
    border-radius: 2px;
    padding: 2px 4px;
    color: #dddddd;
}
QScrollBar:vertical {
    background: #2b2b2b;
    width: 10px;
}
QScrollBar::handle:vertical {
    background: #555;
    border-radius: 5px;
    min-height: 20px;
}
QCheckBox { color: #dddddd; }
QLabel { color: #dddddd; }
"""
