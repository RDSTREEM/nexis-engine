"""
settings_panel.py
Project settings — physics, tags, layers, render, input bindings.
Saved to <project_root>/project_settings.json
"""
from __future__ import annotations
import json
from pathlib import Path

from PySide6.QtCore    import Qt
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QDoubleSpinBox,
    QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QPushButton,
    QTabWidget, QVBoxLayout, QWidget, QCheckBox,
    QSpinBox, QComboBox,
)


SETTINGS_FILE = "project_settings.json"

DEFAULT_SETTINGS = {
    "physics": {
        "gravity_x":  0.0,
        "gravity_y": -9.81,
        "fixed_timestep": 0.02,
        "max_substeps":   5,
    },
    "render": {
        "target_fps":    60,
        "vsync":         True,
        "msaa_samples":  4,
        "background_color": [0.1, 0.12, 0.18, 1.0],
    },
    "tags":   ["Untagged", "Player", "Enemy", "Ground",
               "Trigger", "UI", "Camera"],
    "layers": ["Default", "UI", "Physics", "Ignore Raycast"],
    "input":  {
        "Horizontal": {"positive": "D", "negative": "A"},
        "Vertical":   {"positive": "W", "negative": "S"},
        "Jump":       {"positive": "Space", "negative": ""},
        "Fire":       {"positive": "Mouse0", "negative": ""},
    },
}


class SettingsPanel(QDialog):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.setWindowTitle("Project Settings")
        self.setMinimumSize(560, 420)
        self._settings = self._load()

        layout = QVBoxLayout(self)
        tabs   = QTabWidget()

        tabs.addTab(self._build_physics_tab(), "Physics")
        tabs.addTab(self._build_render_tab(),  "Render")
        tabs.addTab(self._build_tags_tab(),    "Tags & Layers")
        tabs.addTab(self._build_input_tab(),   "Input")

        layout.addWidget(tabs)

        btns = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    # ------------------------------------------------------------------
    # Physics tab
    # ------------------------------------------------------------------

    def _build_physics_tab(self) -> QWidget:
        w   = QWidget()
        frm = QFormLayout(w)
        p   = self._settings["physics"]

        gx = QDoubleSpinBox(); gx.setRange(-100, 100)
        gx.setValue(p["gravity_x"])
        gx.valueChanged.connect(lambda v: p.update({"gravity_x": v}))
        frm.addRow("Gravity X", gx)

        gy = QDoubleSpinBox(); gy.setRange(-100, 100)
        gy.setValue(p["gravity_y"])
        gy.valueChanged.connect(lambda v: p.update({"gravity_y": v}))
        frm.addRow("Gravity Y", gy)

        ts = QDoubleSpinBox(); ts.setRange(0.001, 0.1)
        ts.setDecimals(4); ts.setValue(p["fixed_timestep"])
        ts.valueChanged.connect(lambda v: p.update({"fixed_timestep": v}))
        frm.addRow("Fixed Timestep", ts)

        ms = QSpinBox(); ms.setRange(1, 20)
        ms.setValue(p["max_substeps"])
        ms.valueChanged.connect(lambda v: p.update({"max_substeps": v}))
        frm.addRow("Max Substeps", ms)
        return w

    # ------------------------------------------------------------------
    # Render tab
    # ------------------------------------------------------------------

    def _build_render_tab(self) -> QWidget:
        w   = QWidget()
        frm = QFormLayout(w)
        r   = self._settings["render"]

        fps = QSpinBox(); fps.setRange(10, 300); fps.setValue(r["target_fps"])
        fps.valueChanged.connect(lambda v: r.update({"target_fps": v}))
        frm.addRow("Target FPS", fps)

        vs = QCheckBox(); vs.setChecked(r["vsync"])
        vs.toggled.connect(lambda v: r.update({"vsync": v}))
        frm.addRow("VSync", vs)

        msaa = QComboBox(); msaa.addItems(["1", "2", "4", "8"])
        msaa.setCurrentText(str(r["msaa_samples"]))
        msaa.currentTextChanged.connect(
            lambda v: r.update({"msaa_samples": int(v)}))
        frm.addRow("MSAA Samples", msaa)
        return w

    # ------------------------------------------------------------------
    # Tags & Layers tab
    # ------------------------------------------------------------------

    def _build_tags_tab(self) -> QWidget:
        w      = QWidget()
        layout = QHBoxLayout(w)

        def _list_editor(title, items_ref):
            col = QWidget(); v = QVBoxLayout(col)
            v.addWidget(QLabel(title))
            lw = QListWidget()
            for t in items_ref:
                lw.addItem(QListWidgetItem(t))
            v.addWidget(lw)
            row = QHBoxLayout()
            ed  = QLineEdit(); ed.setPlaceholderText("New…")
            add = QPushButton("+"); add.setFixedWidth(28)
            rem = QPushButton("✕"); rem.setFixedWidth(28)

            def _add():
                txt = ed.text().strip()
                if txt and txt not in items_ref:
                    items_ref.append(txt)
                    lw.addItem(txt)
                    ed.clear()

            def _rem():
                row_idx = lw.currentRow()
                if row_idx >= 1:   # protect index 0
                    items_ref.pop(row_idx)
                    lw.takeItem(row_idx)

            add.clicked.connect(_add)
            rem.clicked.connect(_rem)
            row.addWidget(ed); row.addWidget(add); row.addWidget(rem)
            v.addLayout(row)
            return col

        layout.addWidget(_list_editor("Tags",   self._settings["tags"]))
        layout.addWidget(_list_editor("Layers", self._settings["layers"]))
        return w

    # ------------------------------------------------------------------
    # Input tab
    # ------------------------------------------------------------------

    def _build_input_tab(self) -> QWidget:
        w      = QWidget()
        layout = QVBoxLayout(w)
        inp    = self._settings["input"]

        frm = QFormLayout()
        self._input_widgets = {}
        for axis, bindings in inp.items():
            pos = QLineEdit(bindings.get("positive", ""))
            neg = QLineEdit(bindings.get("negative", ""))
            pos.textChanged.connect(
                lambda v, a=axis: inp[a].update({"positive": v}))
            neg.textChanged.connect(
                lambda v, a=axis: inp[a].update({"negative": v}))
            row = QHBoxLayout()
            row.addWidget(QLabel("+")); row.addWidget(pos)
            row.addWidget(QLabel("-")); row.addWidget(neg)
            wrapper = QWidget(); wrapper.setLayout(row)
            frm.addRow(axis, wrapper)
        layout.addLayout(frm)

        add_btn = QPushButton("+ Add Axis")
        add_btn.clicked.connect(lambda: self._add_axis(frm, inp))
        layout.addWidget(add_btn)
        layout.addStretch()
        return w

    def _add_axis(self, frm, inp):
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "New Axis", "Axis name:")
        if ok and name.strip() and name not in inp:
            inp[name] = {"positive": "", "negative": ""}
            pos = QLineEdit(); neg = QLineEdit()
            pos.textChanged.connect(
                lambda v, a=name: inp[a].update({"positive": v}))
            neg.textChanged.connect(
                lambda v, a=name: inp[a].update({"negative": v}))
            row = QHBoxLayout()
            row.addWidget(QLabel("+")); row.addWidget(pos)
            row.addWidget(QLabel("-")); row.addWidget(neg)
            wrapper = QWidget(); wrapper.setLayout(row)
            frm.addRow(name, wrapper)

    # ------------------------------------------------------------------
    # Load / Save
    # ------------------------------------------------------------------

    def _load(self) -> dict:
        import copy
        base = copy.deepcopy(DEFAULT_SETTINGS)
        root = self.app.project.project_root
        if root:
            p = root / SETTINGS_FILE
            if p.exists():
                try:
                    saved = json.loads(p.read_text(encoding="utf-8"))
                    # deep merge
                    for k, v in saved.items():
                        if isinstance(v, dict) and k in base:
                            base[k].update(v)
                        else:
                            base[k] = v
                except Exception:
                    pass
        return base

    def _save(self) -> None:
        root = self.app.project.project_root
        if root:
            p = root / SETTINGS_FILE
            p.write_text(
                json.dumps(self._settings, indent=2), encoding="utf-8")
            # apply physics gravity live
            play = getattr(self.app, "play_mode", None)
            if play:
                from core.physics_2d import PhysicsWorld2D
                gx = self._settings["physics"]["gravity_x"]
                gy = self._settings["physics"]["gravity_y"]
                play._physics.gravity[:] = (gx, gy)
            self.app.console.info("Project settings saved.")
        self.accept()


def open_settings(app, parent=None) -> None:
    dlg = SettingsPanel(app, parent)
    dlg.exec()