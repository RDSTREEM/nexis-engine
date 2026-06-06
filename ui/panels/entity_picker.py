"""
entity_picker.py
"Create Entity" dialog — shows categorised entity templates with descriptions.
Replaces the plain text QInputDialog for adding entities.
"""
from __future__ import annotations
from PySide6.QtCore    import Qt
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QHBoxLayout,
    QLabel, QListWidget, QListWidgetItem,
    QVBoxLayout, QWidget, QLineEdit,
)
from core.entity_templates import TEMPLATES


class EntityPickerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Entity")
        self.setMinimumSize(500, 380)
        self._chosen_key: str = ""

        layout = QVBoxLayout(self)

        # search bar
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search templates…")
        self._search.textChanged.connect(self._filter)
        layout.addWidget(self._search)

        # main area: category list + template list + description
        row = QHBoxLayout()

        # categories
        self._cat_list = QListWidget()
        self._cat_list.setFixedWidth(110)
        categories = ["All"] + sorted({v[1] for v in TEMPLATES.values()})
        for cat in categories:
            self._cat_list.addItem(cat)
        self._cat_list.setCurrentRow(0)
        self._cat_list.currentTextChanged.connect(self._filter)
        row.addWidget(self._cat_list)

        # templates
        self._tmpl_list = QListWidget()
        self._tmpl_list.currentItemChanged.connect(self._on_select)
        self._tmpl_list.itemDoubleClicked.connect(self._on_double_click)
        row.addWidget(self._tmpl_list)

        # description panel
        desc_panel = QWidget()
        desc_panel.setFixedWidth(160)
        dp_lay = QVBoxLayout(desc_panel)
        dp_lay.setContentsMargins(4, 4, 4, 4)
        self._desc_title = QLabel("")
        self._desc_title.setWordWrap(True)
        self._desc_title.setStyleSheet("font-weight:bold;color:#ddd;")
        self._desc_body  = QLabel("")
        self._desc_body.setWordWrap(True)
        self._desc_body.setStyleSheet("color:#aaa;font-size:10px;")
        dp_lay.addWidget(self._desc_title)
        dp_lay.addWidget(self._desc_body)
        dp_lay.addStretch()
        row.addWidget(desc_panel)

        layout.addLayout(row)

        # name override
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Name:"))
        self._name_edit = QLineEdit()
        name_row.addWidget(self._name_edit)
        layout.addLayout(name_row)

        # buttons
        btns = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._on_ok)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        self._populate("All")

    # ------------------------------------------------------------------

    def _populate(self, category: str, search: str = "") -> None:
        self._tmpl_list.clear()
        for key, (fn, cat, desc) in TEMPLATES.items():
            if category != "All" and cat != category:
                continue
            if search and search.lower() not in key.lower():
                continue
            item = QListWidgetItem(key)
            item.setData(Qt.UserRole, key)
            self._tmpl_list.addItem(item)
        if self._tmpl_list.count():
            self._tmpl_list.setCurrentRow(0)

    def _filter(self) -> None:
        cat    = self._cat_list.currentItem()
        cat_txt = cat.text() if cat else "All"
        self._populate(cat_txt, self._search.text().strip())

    def _on_select(self, item) -> None:
        if item is None:
            return
        key = item.data(Qt.UserRole)
        if key and key in TEMPLATES:
            _, cat, desc = TEMPLATES[key]
            self._desc_title.setText(key)
            self._desc_body.setText(desc)
            if not self._name_edit.text():
                self._name_edit.setText(key)

    def _on_double_click(self, _item) -> None:
        self._on_ok()

    def _on_ok(self) -> None:
        item = self._tmpl_list.currentItem()
        if item is None:
            return
        self._chosen_key = item.data(Qt.UserRole)
        self.accept()

    # ------------------------------------------------------------------

    def result(self) -> tuple[str, str]:
        """Returns (template_key, entity_name)."""
        name = self._name_edit.text().strip() or self._chosen_key
        return self._chosen_key, name