"""
tag_selector.py — Tag selection dialog for entity inspector.
Select from predefined project tags with ability to add new ones.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class TagSelectorDialog(QDialog):
    """
    Select tags for an entity from predefined project tags.
    Allows selecting multiple tags and adding new custom tags.
    """

    def __init__(self, current_tags: list, project, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Tags")
        self.setMinimumSize(300, 350)
        self.setStyleSheet(
            "QDialog{background:#242424;} "
            "QListWidget{background:#1a1a1a;color:#ddd;border:1px solid #3a3a3a;} "
            "QLineEdit{background:#1e1e1e;border:1px solid #3a3a3a;color:#ddd;padding:4px;border-radius:3px;} "
            "QPushButton{background:#333;border:1px solid #484848;border-radius:4px;padding:4px 10px;color:#ddd;} "
            "QPushButton:hover{background:#3c3c3c;} "
            "QLabel{color:#ddd;}"
        )
        self.selected_tags = list(current_tags) or []
        self.project = project

        layout = QVBoxLayout(self)

        # Available tags list
        lbl = QLabel("Available Tags:")
        layout.addWidget(lbl)

        self.tag_list = QListWidget()
        self.tag_list.setSelectionMode(QListWidget.MultiSelection)
        self._populate_tags()
        layout.addWidget(self.tag_list)

        # Add custom tag
        custom_row = QHBoxLayout()
        custom_row.addWidget(QLabel("Add Custom:"))
        self.custom_tag_edit = QLineEdit()
        self.custom_tag_edit.setPlaceholderText("new tag name…")
        custom_row.addWidget(self.custom_tag_edit)
        add_btn = QPushButton("+")
        add_btn.setFixedWidth(32)
        add_btn.clicked.connect(self._add_custom_tag)
        custom_row.addWidget(add_btn)
        layout.addLayout(custom_row)

        # Currently selected
        sel_lbl = QLabel("Selected Tags:")
        layout.addWidget(sel_lbl)

        self.selected_list = QListWidget()
        self._update_selected_display()
        layout.addWidget(self.selected_list)

        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._on_accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _populate_tags(self):
        """Fill tag list with available project tags and custom tags."""
        tags = self.project.get_tags()
        for tag in tags:
            item = QListWidgetItem(tag)
            item.setFlags(item.flags() | Qt.ItemIsSelectable)
            self.tag_list.addItem(item)
            if tag in self.selected_tags:
                item.setSelected(True)

    def _add_custom_tag(self):
        """Add a custom tag to selected tags."""
        text = self.custom_tag_edit.text().strip()
        if text and text not in self.selected_tags:
            self.selected_tags.append(text)
            self._update_selected_display()
            self.custom_tag_edit.clear()

    def _update_selected_display(self):
        """Update the selected tags list view."""
        self.selected_list.clear()
        for tag in self.selected_tags:
            item = QListWidgetItem(tag)
            # Add remove button capability via right-click or double-click
            self.selected_list.addItem(item)

    def _on_accept(self):
        """Collect selected tags from the list and any custom tags."""
        selected = []
        for item in self.tag_list.selectedItems():
            tag = item.text()
            if tag not in selected:
                selected.append(tag)

        # Add any custom tags from selected_list
        for tag in self.selected_tags:
            if tag not in selected and tag not in self.tag_list.findItems(
                tag, Qt.MatchExactly
            ):
                selected.append(tag)

        self.selected_tags = selected
        self.accept()
