from __future__ import annotations
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDockWidget,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class SceneListPanel(QDockWidget):
    def __init__(self, app, parent=None):
        super().__init__("Scenes", parent)
        self.app = app
        self.setAllowedAreas(
            Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea
        )

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # toolbar
        bar = QHBoxLayout()
        new_btn = QPushButton("+ Scene")
        new_btn.clicked.connect(self._on_new_scene)
        ref_btn = QPushButton("↺")
        ref_btn.setFixedWidth(28)
        ref_btn.clicked.connect(self.refresh)
        bar.addWidget(new_btn)
        bar.addWidget(ref_btn)
        bar.addStretch()
        layout.addLayout(bar)

        self._list = QListWidget()
        self._list.setDragDropMode(QListWidget.InternalMove)
        self._list.itemDoubleClicked.connect(self._on_load)
        self._list.setContextMenuPolicy(Qt.CustomContextMenu)
        self._list.customContextMenuRequested.connect(self._context_menu)
        layout.addWidget(self._list)

        # startup scene label
        self._startup_lbl = QLabel("Startup: —")
        self._startup_lbl.setStyleSheet("color:#888;font-size:10px;")
        layout.addWidget(self._startup_lbl)

        self.setWidget(container)

    # ------------------------------------------------------------------

    def refresh(self) -> None:
        self._list.clear()
        root = self.app.project.project_root
        if root is None:
            return
        scenes_dir = root / "scenes"
        if not scenes_dir.exists():
            return
        for f in sorted(scenes_dir.glob("*.nexis_scene")):
            item = QListWidgetItem(f.stem)
            item.setData(Qt.UserRole, str(f))
            # mark active scene
            active = self.app.active_scene
            if active and active.name == f.stem:
                item.setForeground(
                    __import__("PySide6.QtGui", fromlist=["QColor"]).QColor("#3c8dde")
                )
            self._list.addItem(item)
        # startup scene
        try:
            import json

            pd = json.loads(self.app.project.project_path.read_text(encoding="utf-8"))
            startup = pd.get("startup_scene", "")
            self._startup_lbl.setText(
                f"Startup: {Path(startup).stem if startup else '—'}"
            )
        except Exception:
            pass

    def _on_load(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.UserRole)
        if path:
            from core.scene_manager_runtime import SceneManager

            SceneManager.load(path)
            self.refresh()

    def _on_new_scene(self) -> None:
        root = self.app.project.project_root
        if root is None:
            self.app.console.warning("Open a project first.")
            return
        from PySide6.QtWidgets import QInputDialog

        name, ok = QInputDialog.getText(
            self, "New Scene", "Scene name:", text="NewScene"
        )
        if not ok or not name.strip():
            return
        import json
        from core.scene import Scene

        scenes_dir = root / "scenes"
        scenes_dir.mkdir(exist_ok=True)
        path = scenes_dir / f"{name.strip()}.nexis_scene"
        scene = Scene(name.strip(), self.app.project.project_type)
        path.write_text(json.dumps(scene.to_dict(), indent=2), encoding="utf-8")
        self.app.console.info(f"Created scene: {path.name}")
        self.refresh()

    def _context_menu(self, pos) -> None:
        item = self._list.itemAt(pos)
        if item is None:
            return
        path = item.data(Qt.UserRole)
        menu = QMenu()
        menu.addAction("Load", lambda: self._on_load(item))
        menu.addAction("Load Additive", lambda: self._load_additive(path))
        menu.addAction("Set as Startup", lambda: self._set_startup(path))
        menu.addSeparator()
        menu.addAction("Delete", lambda: self._delete_scene(path))
        menu.exec(self._list.mapToGlobal(pos))

    def _load_additive(self, path: str) -> None:
        from core.scene_manager_runtime import SceneManager

        SceneManager.load_additive(path)
        self.refresh()

    def _set_startup(self, path: str) -> None:
        import json

        try:
            proj_path = self.app.project.project_path
            data = json.loads(proj_path.read_text(encoding="utf-8"))
            root = self.app.project.project_root
            rel = str(Path(path).relative_to(root))
            data["startup_scene"] = rel
            proj_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            self.app.console.info(f"Startup scene set to: {Path(path).stem}")
            self.refresh()
        except Exception as e:
            self.app.console.warning(f"Could not set startup scene: {e}")

    def _delete_scene(self, path: str) -> None:
        reply = QMessageBox.question(
            self,
            "Delete Scene",
            f"Delete '{Path(path).stem}'? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            Path(path).unlink(missing_ok=True)
            self.refresh()
