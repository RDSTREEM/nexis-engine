from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDockWidget,
    QHBoxLayout,
    QInputDialog,
    QMenu,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from core.entity import Entity


class HierarchyPanel(QDockWidget):
    def __init__(self, app, parent=None):
        super().__init__("Scene Hierarchy", parent)
        self.app = app
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("+ Entity")
        add_btn.clicked.connect(self.on_add_entity)
        del_btn = QPushButton("✕")
        del_btn.setFixedWidth(28)
        del_btn.clicked.connect(self.on_delete_entity)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(del_btn)
        layout.addLayout(btn_row)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Scene")
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._context_menu)
        self.tree.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.tree)

        self.setWidget(container)

    # ------------------------------------------------------------------

    def refresh(self) -> None:
        self.tree.clear()
        scene = self.app.active_scene
        if scene is None:
            return
        root = QTreeWidgetItem([scene.name])
        root.setData(0, Qt.UserRole, None)
        self.tree.addTopLevelItem(root)
        for entity in scene.entities:
            item = QTreeWidgetItem([entity.name])
            item.setData(0, Qt.UserRole, entity.id)
            root.addChild(item)
        root.setExpanded(True)

    def highlight_entity(self, entity: Optional["Entity"]) -> None:
        self.tree.clearSelection()
        if entity is None:
            return
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            r = root.child(i)
            for j in range(r.childCount()):
                child = r.child(j)
                if child.data(0, Qt.UserRole) == entity.id:
                    child.setSelected(True)
                    self.tree.scrollToItem(child)
                    return

    # ------------------------------------------------------------------

    def _on_item_clicked(self, item: QTreeWidgetItem, _col: int) -> None:
        entity_id = item.data(0, Qt.UserRole)
        if entity_id is None:
            self.app.selector.clear()
            return
        scene = self.app.active_scene
        if scene:
            entity = scene.get_entity_by_id(entity_id)
            self.app.selector.select(entity)

    def _context_menu(self, pos) -> None:
        menu = QMenu()
        menu.addAction("Add Entity", self.on_add_entity)
        menu.addAction("Delete Entity", self.on_delete_entity)
        menu.addAction("Rename", self.on_rename_entity)
        menu.exec(self.tree.mapToGlobal(pos))

    # ------------------------------------------------------------------

    def on_add_entity(self) -> None:
        scene = self.app.active_scene
        if not scene:
            return
        name, ok = QInputDialog.getText(
            self, "New Entity", "Entity name:", text="Entity"
        )
        if ok and name.strip():
            scene.create_entity(name.strip())
            self.refresh()

    def on_delete_entity(self) -> None:
        scene = self.app.active_scene
        if not scene:
            return
        item = self.tree.currentItem()
        if not item:
            return
        entity_id = item.data(0, Qt.UserRole)
        if entity_id is None:
            return
        entity = scene.get_entity_by_id(entity_id)
        if not entity:
            return
        reply = QMessageBox.question(
            self,
            "Delete Entity",
            f"Delete '{entity.name}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            scene.remove_entity(entity)
            self.app.selector.clear()
            self.refresh()

    def on_rename_entity(self) -> None:
        item = self.tree.currentItem()
        if not item:
            return
        entity_id = item.data(0, Qt.UserRole)
        if entity_id is None:
            return
        scene = self.app.active_scene
        entity = scene.get_entity_by_id(entity_id) if scene else None
        if not entity:
            return
        name, ok = QInputDialog.getText(self, "Rename", "New name:", text=entity.name)
        if ok and name.strip():
            entity.name = name.strip()
            self.refresh()
