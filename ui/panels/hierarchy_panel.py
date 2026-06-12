"""
hierarchy_panel.py — Reworked.
Consistent header bar, entity colors, search bar.
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDockWidget,
    QHBoxLayout,
    QInputDialog,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
    QLabel,
)

from ui.theme import (
    BG_SURFACE,
    BG_HEADER,
    BG_RAISED,
    BG_INPUT,
    ACCENT,
    ACCENT_DIM,
    BORDER,
    BORDER_LIGHT,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
    TAG_GROUP,
    TAG_LIGHT,
    TAG_AUDIO,
    TAG_DISABLED,
    GREEN,
    GREEN_BG,
    GREEN_BORDER,
    PANEL_TOOLBAR_H,
    ROW_H,
)

if TYPE_CHECKING:
    from core.entity import Entity


class HierarchyPanel(QDockWidget):
    def __init__(self, app, parent=None):
        super().__init__("Hierarchy", parent)
        self.app = app
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        root_w = QWidget()
        root_w.setStyleSheet(f"background: {BG_SURFACE};")
        lay = QVBoxLayout(root_w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # ── Header bar ────────────────────────────────────────────────
        hdr = QWidget()
        hdr.setFixedHeight(PANEL_TOOLBAR_H)
        hdr.setStyleSheet(
            f"background: {BG_HEADER}; border-bottom: 1px solid {BORDER};"
        )
        hdr_row = QHBoxLayout(hdr)
        hdr_row.setContentsMargins(10, 0, 8, 0)
        hdr_row.setSpacing(4)

        self._count_lbl = QLabel("0 entities")
        self._count_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        hdr_row.addWidget(self._count_lbl, 1)

        add_btn = QPushButton("+")
        add_btn.setFixedSize(22, 22)
        add_btn.setToolTip("Add Entity (Ctrl+Shift+A)")
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: {GREEN_BG};
                border: 1px solid {GREEN_BORDER};
                border-radius: 4px;
                color: {GREEN};
                font-weight: 700;
                font-size: 15px;
                padding: 0;
            }}
            QPushButton:hover {{ background: #1f3828; }}
            QPushButton:pressed {{ background: #141f18; }}
        """)
        add_btn.clicked.connect(self.on_add_entity)
        hdr_row.addWidget(add_btn)
        lay.addWidget(hdr)

        # ── Search bar ────────────────────────────────────────────────
        self._search = QLineEdit()
        self._search.setPlaceholderText("  Filter entities…")
        self._search.setFixedHeight(28)
        self._search.setStyleSheet(f"""
            QLineEdit {{
                background: {BG_INPUT};
                border: none;
                border-bottom: 1px solid {BORDER};
                padding: 4px 10px;
                color: {TEXT_SECONDARY};
                font-size: 11px;
            }}
            QLineEdit:focus {{ border-bottom-color: {ACCENT}; color: {TEXT_PRIMARY}; }}
        """)
        self._search.textChanged.connect(self._filter)
        lay.addWidget(self._search)

        # ── Tree ──────────────────────────────────────────────────────
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(16)
        self.tree.setStyleSheet(f"""
            QTreeWidget {{
                background: {BG_SURFACE};
                border: none;
                color: {TEXT_PRIMARY};
                outline: none;
            }}
            QTreeWidget::item {{
                height: {ROW_H}px;
                padding-left: 2px;
            }}
            QTreeWidget::item:hover {{ background: {BG_RAISED}; }}
            QTreeWidget::item:selected {{ background: {ACCENT_DIM}; color: {TEXT_PRIMARY}; }}
            QTreeWidget::branch:has-children:closed {{ image: none; }}
            QTreeWidget::branch:has-children:open {{ image: none; }}
        """)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._context_menu)
        self.tree.itemClicked.connect(self._on_click)
        self.tree.setDragDropMode(QTreeWidget.InternalMove)
        self.tree.setDefaultDropAction(Qt.MoveAction)
        self.tree.model().rowsMoved.connect(self._on_rows_moved)
        lay.addWidget(self.tree, 1)

        self.setWidget(root_w)

    # ── Refresh ────────────────────────────────────────────────────────

    def refresh(self) -> None:
        sel_id = (
            self.app.selector.selected_entity.id
            if self.app.selector.selected_entity
            else None
        )
        self.tree.blockSignals(True)
        self.tree.clear()
        scene = self.app.active_scene
        count = 0
        if scene:
            scene_item = QTreeWidgetItem([f"  {scene.name}"])
            scene_item.setData(0, Qt.UserRole, None)
            scene_item.setForeground(0, QColor(ACCENT))
            self.tree.addTopLevelItem(scene_item)
            for entity in scene.entities:
                count += 1 + len(entity.all_children_recursive())
                item = self._mk(entity)
                scene_item.addChild(item)
                self._add_children(item, entity)
            scene_item.setExpanded(True)
        self._count_lbl.setText(f"{count} entities" if count != 1 else "1 entity")
        self.tree.blockSignals(False)
        if sel_id:
            self._highlight(sel_id)
        filt = self._search.text().strip()
        if filt:
            self._filter(filt)

    def _mk(self, entity: "Entity") -> QTreeWidgetItem:
        enabled_dot = "●" if entity.enabled else "○"
        item = QTreeWidgetItem([f" {enabled_dot}  {entity.name}"])
        item.setData(0, Qt.UserRole, entity.id)
        if not entity.enabled:
            item.setForeground(0, QColor(TAG_DISABLED))
        elif "group" in entity.tags:
            item.setForeground(0, QColor(TAG_GROUP))
        elif "light" in entity.tags:
            item.setForeground(0, QColor(TAG_LIGHT))
        elif "audio" in entity.tags:
            item.setForeground(0, QColor(TAG_AUDIO))
        return item

    def _add_children(self, parent_item, parent_entity) -> None:
        for child in parent_entity.children:
            ci = self._mk(child)
            parent_item.addChild(ci)
            self._add_children(ci, child)
        if parent_entity.children:
            parent_item.setExpanded(True)

    def _highlight(self, eid: str) -> None:
        self._find_and_select(self.tree.invisibleRootItem(), eid)

    def _find_and_select(self, parent, eid: str) -> bool:
        for i in range(parent.childCount()):
            child = parent.child(i)
            if child.data(0, Qt.UserRole) == eid:
                child.setSelected(True)
                self.tree.scrollToItem(child)
                return True
            if self._find_and_select(child, eid):
                return True
        return False

    def _filter(self, text: str) -> None:
        text = text.lower().strip()
        self._filter_items(self.tree.invisibleRootItem(), text)

    def _filter_items(self, parent, text: str) -> bool:
        any_vis = False
        for i in range(parent.childCount()):
            child = parent.child(i)
            label = child.text(0).lower()
            child_vis = self._filter_items(child, text) or (not text) or (text in label)
            child.setHidden(not child_vis)
            any_vis = any_vis or child_vis
        return any_vis

    # ── Drag-drop ──────────────────────────────────────────────────────

    def _on_rows_moved(self, *_) -> None:
        scene = self.app.active_scene
        if scene is None:
            return
        root = self.tree.invisibleRootItem()
        if root.childCount() == 0:
            return
        self._sync(root.child(0), None, scene)

    def _sync(self, tree_item, parent_entity, scene) -> None:
        for i in range(tree_item.childCount()):
            ci = tree_item.child(i)
            eid = ci.data(0, Qt.UserRole)
            e = scene.get_entity_by_id(eid) if eid else None
            if e is None:
                continue
            if parent_entity is None:
                if e._parent is not None:
                    e.detach_from_parent()
                if e not in scene._entities:
                    scene._entities.append(e)
            else:
                if e._parent is not parent_entity:
                    if e in scene._entities:
                        scene._entities.remove(e)
                    parent_entity.add_child(e)
            self._sync(ci, e, scene)

    # ── Selection ──────────────────────────────────────────────────────

    def _on_click(self, item: QTreeWidgetItem, _col: int) -> None:
        eid = item.data(0, Qt.UserRole)
        if eid is None:
            self.app.selector.clear()
            return
        scene = self.app.active_scene
        entity = scene.get_entity_by_id(eid) if scene else None
        self.app.selector.select(entity)

    # ── Context menu ───────────────────────────────────────────────────

    def _context_menu(self, pos) -> None:
        item = self.tree.itemAt(pos)
        menu = QMenu()
        menu.addAction("Add Entity", self.on_add_entity)
        if item and item.data(0, Qt.UserRole):
            menu.addAction("Add Child", self._on_add_child)
            menu.addAction("Duplicate", self._on_duplicate)
            menu.addAction("Group", self._on_group)
            menu.addSeparator()
            menu.addAction("Save as Prefab", self._on_prefab)
            menu.addSeparator()
            menu.addAction("Rename", self.on_rename_entity)
            menu.addAction("Delete", self.on_delete_entity)
        menu.exec(self.tree.mapToGlobal(pos))

    # ── Operations ─────────────────────────────────────────────────────

    def on_add_entity(self) -> None:
        scene = self.app.active_scene
        if not scene:
            return
        from ui.panels.entity_picker import EntityPickerDialog
        from core.entity_templates import TEMPLATES

        dlg = EntityPickerDialog(self)
        if dlg.exec():
            key, name = dlg.result()
            if key in TEMPLATES:
                fn = TEMPLATES[key][0]
                entity = fn(scene)
                entity.name = name or entity.name
                from core.undo_redo import AddEntityCommand, UndoStack

                UndoStack.execute(AddEntityCommand(scene, entity))
                self.refresh()
                self.app.selector.select(entity)

    def _on_add_child(self) -> None:
        scene = self.app.active_scene
        parent = self.app.selector.selected_entity
        if not scene or not parent:
            return
        from ui.panels.entity_picker import EntityPickerDialog
        from core.entity_templates import TEMPLATES

        dlg = EntityPickerDialog(self)
        if dlg.exec():
            key, name = dlg.result()
            if key in TEMPLATES:
                fn = TEMPLATES[key][0]
                child = fn(scene)
                child.name = name or child.name
                parent.add_child(child)
                self.refresh()
                self.app.selector.select(child)

    def _on_group(self) -> None:
        scene = self.app.active_scene
        entity = self.app.selector.selected_entity
        if not scene or not entity:
            return
        from core.entity_templates import group_entity

        group = group_entity(scene, "Group")
        old_p = entity._parent
        if old_p:
            old_p.add_child(group)
        else:
            scene.add_entity(group)
        group.add_child(entity)
        self.refresh()
        self.app.selector.select(group)

    def on_delete_entity(self) -> None:
        scene = self.app.active_scene
        entity = self.app.selector.selected_entity
        if not scene or not entity:
            return
        reply = QMessageBox.question(
            self,
            "Delete",
            f"Delete '{entity.name}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            from core.undo_redo import DeleteEntityCommand, UndoStack

            UndoStack.execute(DeleteEntityCommand(scene, entity))
            self.app.selector.clear()
            self.refresh()

    def on_rename_entity(self) -> None:
        entity = self.app.selector.selected_entity
        if not entity:
            return
        name, ok = QInputDialog.getText(self, "Rename", "New name:", text=entity.name)
        if ok and name.strip():
            entity.name = name.strip()
            self.refresh()

    def _on_duplicate(self) -> None:
        import uuid

        scene = self.app.active_scene
        entity = self.app.selector.selected_entity
        if not scene or not entity:
            return
        from core.entity import Entity

        data = entity.to_dict()
        data["id"] = str(uuid.uuid4())
        data["name"] = entity.name + " (copy)"
        copy = Entity.from_dict(data, scene=scene)
        copy.transform.position[0] += 0.5
        copy.transform._dirty = True
        if entity._parent:
            entity._parent.add_child(copy)
        else:
            scene.add_entity(copy)
        self.refresh()
        self.app.selector.select(copy)

    def _on_prefab(self) -> None:
        entity = self.app.selector.selected_entity
        if entity:
            self.app.prefabs.save_prefab(entity)
