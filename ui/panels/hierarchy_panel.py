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
        self.tree.itemClicked.connect(self._on_item_clicked)
        # allow drag-drop for reparenting
        self.tree.setDragDropMode(QTreeWidget.InternalMove)
        self.tree.setDefaultDropAction(Qt.MoveAction)
        self.tree.model().rowsMoved.connect(self._on_rows_moved)
        layout.addWidget(self.tree)
        self.setWidget(container)

    # ------------------------------------------------------------------
    # Refresh — builds full nested tree
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        selected_id = (self.app.selector.selected_entity.id
                       if self.app.selector.selected_entity else None)
        self.tree.blockSignals(True)
        self.tree.clear()
        scene = self.app.active_scene
        if scene:
            scene_root = QTreeWidgetItem([scene.name])
            scene_root.setData(0, Qt.UserRole, None)
            self.tree.addTopLevelItem(scene_root)
            for entity in scene.entities:
                item = self._make_item(entity)
                scene_root.addChild(item)
                self._add_children(item, entity)
            scene_root.setExpanded(True)
        self.tree.blockSignals(False)
        if selected_id:
            self._highlight_id(selected_id)

    def _make_item(self, entity: "Entity") -> QTreeWidgetItem:
        item = QTreeWidgetItem([entity.name])
        item.setData(0, Qt.UserRole, entity.id)
        if not entity.enabled:
            from PySide6.QtGui import QColor
            item.setForeground(0, QColor("#666666"))
        if "group" in entity.tags:
            item.setForeground(0, __import__("PySide6.QtGui", fromlist=["QColor"]).QColor("#aaddff"))
        return item

    def _add_children(self, parent_item: QTreeWidgetItem,
                      parent_entity: "Entity") -> None:
        for child in parent_entity.children:
            child_item = self._make_item(child)
            parent_item.addChild(child_item)
            self._add_children(child_item, child)
        if parent_entity.children:
            parent_item.setExpanded(True)

    def _highlight_id(self, eid: str) -> None:
        it = self.tree.invisibleRootItem()
        self._search_and_select(it, eid)

    def _search_and_select(self, parent: QTreeWidgetItem,
                           eid: str) -> bool:
        for i in range(parent.childCount()):
            child = parent.child(i)
            if child.data(0, Qt.UserRole) == eid:
                child.setSelected(True)
                self.tree.scrollToItem(child)
                return True
            if self._search_and_select(child, eid):
                return True
        return False

    # ------------------------------------------------------------------
    # Drag-drop reparenting
    # ------------------------------------------------------------------

    def _on_rows_moved(self, *_args) -> None:
        """
        After a drag-drop reorder, rebuild parent/child relationships
        by reading the tree structure.
        """
        scene = self.app.active_scene
        if scene is None:
            return
        # read new structure from tree
        root = self.tree.invisibleRootItem()
        if root.childCount() == 0:
            return
        scene_item = root.child(0)
        self._sync_hierarchy_from_tree(scene_item, None, scene)

    def _sync_hierarchy_from_tree(self, tree_item, parent_entity, scene):
        for i in range(tree_item.childCount()):
            child_item = tree_item.child(i)
            eid    = child_item.data(0, Qt.UserRole)
            entity = scene.get_entity_by_id(eid) if eid else None
            if entity is None:
                continue
            # reparent if needed
            if parent_entity is None:
                # should be top-level
                if entity._parent is not None:
                    entity.detach_from_parent()
                if entity not in scene._entities:
                    scene._entities.append(entity)
            else:
                if entity._parent is not parent_entity:
                    if entity in scene._entities:
                        scene._entities.remove(entity)
                    parent_entity.add_child(entity)
            self._sync_hierarchy_from_tree(child_item, entity, scene)

    # ------------------------------------------------------------------
    # Click
    # ------------------------------------------------------------------

    def _on_item_clicked(self, item: QTreeWidgetItem, _col: int) -> None:
        eid = item.data(0, Qt.UserRole)
        if eid is None:
            self.app.selector.clear()
            return
        scene  = self.app.active_scene
        entity = scene.get_entity_by_id(eid) if scene else None
        self.app.selector.select(entity)

    # ------------------------------------------------------------------
    # Context menu
    # ------------------------------------------------------------------

    def _context_menu(self, pos) -> None:
        item = self.tree.itemAt(pos)
        menu = QMenu()
        menu.addAction("Add Entity",    self.on_add_entity)
        if item and item.data(0, Qt.UserRole):
            menu.addAction("Add Child Entity", self._on_add_child)
            menu.addAction("Group Selected",   self._on_group_selected)
            menu.addAction("Duplicate",        self._on_duplicate)
            menu.addSeparator()
            menu.addAction("Save as Prefab",   self._on_save_prefab)
            menu.addSeparator()
            menu.addAction("Rename",           self.on_rename_entity)
            menu.addAction("Delete Entity",    self.on_delete_entity)
        menu.exec(self.tree.mapToGlobal(pos))

    # ------------------------------------------------------------------
    # Entity operations
    # ------------------------------------------------------------------

    def on_add_entity(self) -> None:
        scene = self.app.active_scene
        if not scene:
            return
        from ui.panels.entity_picker import EntityPickerDialog
        from core.entity_templates   import TEMPLATES
        dlg = EntityPickerDialog(self)
        if dlg.exec():
            key, name = dlg.result()
            if key in TEMPLATES:
                fn     = TEMPLATES[key][0]
                entity = fn(scene)
                entity.name = name or entity.name
                scene.add_entity(entity)
                self.refresh()
                self.app.selector.select(entity)

    def _on_add_child(self) -> None:
        scene  = self.app.active_scene
        parent = self.app.selector.selected_entity
        if not scene or not parent:
            return
        from ui.panels.entity_picker import EntityPickerDialog
        from core.entity_templates   import TEMPLATES
        dlg = EntityPickerDialog(self)
        if dlg.exec():
            key, name = dlg.result()
            if key in TEMPLATES:
                fn    = TEMPLATES[key][0]
                child = fn(scene)
                child.name = name or child.name
                parent.add_child(child)
                self.refresh()
                self.app.selector.select(child)

    def _on_group_selected(self) -> None:
        """Wrap selected entity in a Group parent."""
        scene  = self.app.active_scene
        entity = self.app.selector.selected_entity
        if not scene or not entity:
            return
        from core.entity_templates import group_entity
        group = group_entity(scene, "Group")
        # insert group at same level as entity
        old_parent = entity._parent
        if old_parent:
            old_parent.add_child(group)
        else:
            scene.add_entity(group)
        group.add_child(entity)
        self.refresh()
        self.app.selector.select(group)

    def on_delete_entity(self) -> None:
        scene  = self.app.active_scene
        entity = self.app.selector.selected_entity
        if not scene or not entity:
            return
        reply = QMessageBox.question(
            self, "Delete", f"Delete '{entity.name}' and all children?",
            QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            scene.remove_entity(entity)
            self.app.selector.clear()
            self.refresh()

    def on_rename_entity(self) -> None:
        entity = self.app.selector.selected_entity
        if not entity:
            return
        name, ok = QInputDialog.getText(
            self, "Rename", "New name:", text=entity.name)
        if ok and name.strip():
            entity.name = name.strip()
            self.refresh()

    def _on_duplicate(self) -> None:
        import json, uuid
        scene  = self.app.active_scene
        entity = self.app.selector.selected_entity
        if not scene or not entity:
            return
        from core.entity import Entity
        data         = entity.to_dict()
        data["id"]   = str(uuid.uuid4())
        data["name"] = entity.name + " (copy)"
        copy         = Entity.from_dict(data, scene=scene)
        copy.transform.position[0] += 0.5
        copy.transform._dirty = True
        if entity._parent:
            entity._parent.add_child(copy)
        else:
            scene.add_entity(copy)
        self.refresh()
        self.app.selector.select(copy)

    def _on_save_prefab(self) -> None:
        entity = self.app.selector.selected_entity
        if not entity:
            return
        self.app.prefabs.save_prefab(entity)