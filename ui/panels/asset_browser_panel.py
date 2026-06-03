"""
asset_browser_panel.py
Shows imported assets grouped by type.
Double-click a mesh asset to add it to the scene.
Double-click a texture to assign to selected entity's material.
"""

from __future__ import annotations
from pathlib import Path

from PySide6.QtCore import Qt, QMimeData, QUrl
from PySide6.QtGui import QDrag, QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDockWidget,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class AssetBrowserPanel(QDockWidget):
    def __init__(self, app, parent=None):
        super().__init__("Asset Browser", parent)
        self.app = app
        self.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.LeftDockWidgetArea)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # toolbar
        bar = QHBoxLayout()
        import_btn = QPushButton("Import…")
        import_btn.clicked.connect(self._on_import)
        refresh_btn = QPushButton("↺")
        refresh_btn.setFixedWidth(28)
        refresh_btn.setToolTip("Rescan project assets folder")
        refresh_btn.clicked.connect(self.refresh)
        bar.addWidget(import_btn)
        bar.addWidget(refresh_btn)
        bar.addStretch()
        layout.addLayout(bar)

        # tabs per asset type
        self._tabs = QTabWidget()
        self._lists: dict[str, QListWidget] = {}
        for atype in ("mesh", "texture", "audio", "script"):
            lw = QListWidget()
            lw.setSelectionMode(QAbstractItemView.SingleSelection)
            lw.setContextMenuPolicy(Qt.CustomContextMenu)
            lw.customContextMenuRequested.connect(
                lambda pos, t=atype: self._context_menu(pos, t)
            )
            lw.itemDoubleClicked.connect(
                lambda item, t=atype: self._on_double_click(item, t)
            )
            self._lists[atype] = lw
            self._tabs.addTab(lw, atype.capitalize())

        layout.addWidget(self._tabs)
        self.setWidget(container)

    # ------------------------------------------------------------------

    def refresh(self) -> None:
        for lw in self._lists.values():
            lw.clear()

        for asset in self.app.assets.all_assets():
            lw = self._lists.get(asset.asset_type)
            if lw is None:
                continue
            item = QListWidgetItem(asset.name)
            item.setData(Qt.UserRole, asset.path)
            item.setToolTip(asset.path)
            lw.addItem(item)

    def _on_import(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Import Assets",
            str(self.app.project.project_root or Path.home()),
            "All Supported (*.obj *.gltf *.glb *.fbx "
            "*.png *.jpg *.jpeg *.bmp *.tga "
            "*.wav *.mp3 *.ogg *.flac "
            "*.py *.amh);;"
            "Meshes (*.obj *.gltf *.glb *.fbx);;"
            "Textures (*.png *.jpg *.jpeg *.bmp *.tga);;"
            "Audio (*.wav *.mp3 *.ogg *.flac);;"
            "Scripts (*.py *.amh)",
        )
        for p in paths:
            self.app.assets.import_file(p)
        self.refresh()

    def _on_double_click(self, item: QListWidgetItem, atype: str) -> None:
        path = item.data(Qt.UserRole)
        if atype == "mesh":
            self._add_mesh_to_scene(path)
        elif atype == "texture":
            self._assign_texture(path)
        elif atype == "audio":
            asset = self.app.assets.get(path)
            if asset and asset.data:
                asset.data.play()
                self.app.console.info(f"Playing audio: {asset.name}")

    def _add_mesh_to_scene(self, path: str) -> None:
        scene = self.app.active_scene
        if scene is None:
            self.app.console.warning("No active scene — open a project first.")
            return
        asset = self.app.assets.get(path)
        if asset is None:
            return
        from core.mesh_renderer import MeshRenderer

        entity = scene.create_entity(asset.name)
        mr = MeshRenderer()
        mr.set_mesh_data(asset.data)
        entity.add_component(mr)
        self.app.main_window.hierarchy.refresh()
        self.app.console.info(f"Added mesh '{asset.name}' to scene.")

    def _assign_texture(self, path: str) -> None:
        sel = self.app.selector.selected_entity
        if sel is None:
            self.app.console.warning("Select an entity first to assign texture.")
            return
        from core.mesh_renderer import MeshRenderer
        from core.sprite_renderer import SpriteRenderer

        asset = self.app.assets.get(path)
        if asset is None or asset.data is None:
            return
        ctx = self.app.main_window.viewport.ctx
        if ctx is None:
            self.app.console.warning("GL context not ready.")
            return
        tex = asset.data.upload_to_gpu(ctx)
        mr = sel.get_component(MeshRenderer) or sel.get_component(SpriteRenderer)
        if mr:
            mr.material.set_texture(tex)
            self.app.console.info(f"Assigned texture '{asset.name}' to '{sel.name}'.")
        else:
            self.app.console.warning(
                f"'{sel.name}' has no MeshRenderer or SpriteRenderer."
            )

    def _context_menu(self, pos, atype: str) -> None:
        lw = self._lists[atype]
        item = lw.itemAt(pos)
        if item is None:
            return
        menu = QMenu()
        if atype == "mesh":
            menu.addAction(
                "Add to Scene", lambda: self._add_mesh_to_scene(item.data(Qt.UserRole))
            )
        elif atype == "texture":
            menu.addAction(
                "Assign to Selected",
                lambda: self._assign_texture(item.data(Qt.UserRole)),
            )
        elif atype == "audio":
            menu.addAction("Preview", lambda: self._on_double_click(item, atype))
        path = item.data(Qt.UserRole)
        menu.addAction("Show in Explorer", lambda: self._show_in_explorer(path))
        menu.exec(lw.mapToGlobal(pos))

    @staticmethod
    def _show_in_explorer(path: str) -> None:
        import subprocess, sys

        p = Path(path).parent
        if sys.platform == "win32":
            subprocess.Popen(["explorer", str(p)])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(p)])
        else:
            subprocess.Popen(["xdg-open", str(p)])
