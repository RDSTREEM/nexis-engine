from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDockWidget, QHBoxLayout, QInputDialog, QMenu,
    QMessageBox, QPushButton, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget,
)

if TYPE_CHECKING:
    from core.entity import Entity


class HierarchyPanel(QDockWidget):
    def __init__(self, app, parent=None):
        super().__init__("Scene Hierarchy", parent)
        self.app = app
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        container = QWidget()
        layout    = QVBoxLayout(container)
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
        # single click selects + pushes to inspector
        self.tree.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.tree)

        self.setWidget(container)

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        # remember currently selected id so we can re-highlight after rebuild
        selected_id = None
        if self.app.selector.selected_entity:
            selected_id = self.app.selector.selected_entity.id

        self.tree.blockSignals(True)
        self.tree.clear()
        scene = self.app.active_scene
        if scene is None:
            self.tree.blockSignals(False)
            return

        root = QTreeWidgetItem([scene.name])
        root.setData(0, Qt.UserRole, None)
        self.tree.addTopLevelItem(root)

        for entity in scene.entities:
            item = QTreeWidgetItem([entity.name])
            item.setData(0, Qt.UserRole, entity.id)
            # dim disabled entities
            if not entity.enabled:
                item.setForeground(0, item.foreground(0))
                from PySide6.QtGui import QColor
                item.setForeground(0, QColor("#666666"))
            root.addChild(item)

        root.setExpanded(True)
        self.tree.blockSignals(False)

        # restore highlight without triggering sync again
        if selected_id:
            self._highlight_id(selected_id)

    def _highlight_id(self, entity_id: str) -> None:
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            r = root.child(i)
            for j in range(r.childCount()):
                child = r.child(j)
                if child.data(0, Qt.UserRole) == entity_id:
                    child.setSelected(True)
                    self.tree.scrollToItem(child)
                    return

    # ------------------------------------------------------------------
    # Item click → select entity → push to inspector via selector
    # ------------------------------------------------------------------

    def _on_item_clicked(self, item: QTreeWidgetItem, _col: int) -> None:
        entity_id = item.data(0, Qt.UserRole)
        if entity_id is None:
            # clicked the scene root row
            self.app.selector.clear()
            return
        scene = self.app.active_scene
        if scene is None:
            return
        entity = scene.get_entity_by_id(entity_id)
        # selector.select() calls sync_to_ui() which updates inspector
        self.app.selector.select(entity)

    # ------------------------------------------------------------------
    # Context menu
    # ------------------------------------------------------------------

    def _context_menu(self, pos) -> None:
        menu = QMenu()
        menu.addAction("Add Entity",    self.on_add_entity)
        menu.addAction("Delete Entity", self.on_delete_entity)
        menu.addAction("Rename",        self.on_rename_entity)
        menu.addSeparator()
        # duplicate
        menu.addAction("Duplicate",     self._on_duplicate)
        menu.exec(self.tree.mapToGlobal(pos))

    # ------------------------------------------------------------------
    # Entity operations
    # ------------------------------------------------------------------

    def on_add_entity(self) -> None:
        scene = self.app.active_scene
        if not scene:
            return
        name, ok = QInputDialog.getText(
            self, "New Entity", "Name:", text="Entity")
        if ok and name.strip():
            entity = scene.create_entity(name.strip())
            self.refresh()
            # auto-select the new entity
            self.app.selector.select(entity)

    def on_delete_entity(self) -> None:
        scene = self.app.active_scene
        if not scene:
            return
        entity = self.app.selector.selected_entity
        if entity is None:
            # fall back to tree selection
            item = self.tree.currentItem()
            if item is None:
                return
            eid = item.data(0, Qt.UserRole)
            if eid is None:
                return
            entity = scene.get_entity_by_id(eid)
        if entity is None:
            return
        reply = QMessageBox.question(
            self, "Delete Entity", f"Delete '{entity.name}'?",
            QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            scene.remove_entity(entity)
            self.app.selector.clear()
            self.refresh()

    def on_rename_entity(self) -> None:
        entity = self.app.selector.selected_entity
        if entity is None:
            item = self.tree.currentItem()
            if item is None:
                return
            eid  = item.data(0, Qt.UserRole)
            if eid is None:
                return
            scene  = self.app.active_scene
            entity = scene.get_entity_by_id(eid) if scene else None
        if entity is None:
            return
        name, ok = QInputDialog.getText(
            self, "Rename", "New name:", text=entity.name)
        if ok and name.strip():
            entity.name = name.strip()
            self.refresh()

    def _on_duplicate(self) -> None:
        import json
        scene  = self.app.active_scene
        entity = self.app.selector.selected_entity
        if scene is None or entity is None:
            return
        from core.entity import Entity
        data        = entity.to_dict()
        import uuid
        data["id"]   = str(uuid.uuid4())
        data["name"] = entity.name + " (copy)"
        copy        = Entity.from_dict(data, scene=scene)
        # offset position slightly so it's visible
        copy.transform.position[0] += 0.5
        copy.transform._dirty = True
        scene.add_entity(copy)
        self.refresh()
        self.app.selector.select(copy)