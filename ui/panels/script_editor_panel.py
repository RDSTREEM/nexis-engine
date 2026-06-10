"""
script_editor_panel.py
Script editor with Amharic syntax highlighting.
Supports both .py (Python) and .amh (Amharic) files.
Shows transpiled Python output in a split view for .amh files.
"""
from __future__ import annotations
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import (
    QColor, QFont, QSyntaxHighlighter, QTextCharFormat, QTextDocument,
)
from PySide6.QtWidgets import (
    QDockWidget, QFileDialog, QHBoxLayout, QLabel,
    QPlainTextEdit, QPushButton, QSplitter, QVBoxLayout, QWidget,
)


# ── Highlighter ───────────────────────────────────────────────────────────────

class _AmharicHighlighter(QSyntaxHighlighter):
    def __init__(self, doc: QTextDocument):
        super().__init__(doc)
        from scripting.amharic_transpiler import get_amharic_keywords

        def fmt(hex_color, bold=False):
            f = QTextCharFormat()
            f.setForeground(QColor(hex_color))
            if bold:
                f.setFontWeight(700)
            return f

        amh_kw  = get_amharic_keywords()
        py_kw   = ["def","class","if","elif","else","while","for","in",
                    "return","break","continue","pass","and","or","not",
                    "True","False","None","import","from","as","try",
                    "except","finally","raise","global","print","self"]

        import re
        self._rules = []
        # Amharic keywords
        for kw in amh_kw:
            self._rules.append((re.compile(rf'\b{re.escape(kw)}\b'),
                                 fmt("#c792ea", bold=True)))
        # Python keywords
        for kw in py_kw:
            self._rules.append((re.compile(rf'\b{kw}\b'),
                                 fmt("#82aaff", bold=True)))
        # Numbers
        self._rules.append((re.compile(r'\b\d+(\.\d+)?\b'), fmt("#f78c6c")))
        # Strings
        self._rules.append((re.compile(r'"[^"\\]*(?:\\.[^"\\]*)*"'), fmt("#c3e88d")))
        self._rules.append((re.compile(r"'[^'\\]*(?:\\.[^'\\]*)*'"), fmt("#c3e88d")))
        # Comments
        self._rules.append((re.compile(r'#[^\n]*'), fmt("#546e7a", bold=False)))
        # self
        self._rules.append((re.compile(r'\bself\b'), fmt("#ff9cac")))
        # Function/class names after def/ተግባር/class/ክፍል
        self._rules.append((re.compile(
            r'(?:def|ተግባር|class|ክፍል)\s+([A-Za-z_\u1200-\u137F][A-Za-z0-9_\u1200-\u137F]*)'),
            fmt("#ffcb6b")))

    def highlightBlock(self, text: str) -> None:
        for pattern, fmt in self._rules:
            for m in pattern.finditer(text):
                start = m.start()
                length = m.end() - start
                self.setFormat(start, length, fmt)


class _PyHighlighter(QSyntaxHighlighter):
    def __init__(self, doc: QTextDocument):
        super().__init__(doc)
        import re

        def fmt(hex_color, bold=False):
            f = QTextCharFormat()
            f.setForeground(QColor(hex_color))
            if bold: f.setFontWeight(700)
            return f

        kw = ["def","class","if","elif","else","while","for","in","return",
              "break","continue","pass","and","or","not","True","False","None",
              "import","from","as","try","except","finally","raise","global","print","self"]
        self._rules = []
        for k in kw:
            self._rules.append((re.compile(rf'\b{k}\b'), fmt("#82aaff", bold=True)))
        self._rules.append((re.compile(r'\b\d+(\.\d+)?\b'),         fmt("#f78c6c")))
        self._rules.append((re.compile(r'"[^"\\]*(?:\\.[^"\\]*)*"'), fmt("#c3e88d")))
        self._rules.append((re.compile(r"'[^'\\]*(?:\\.[^'\\]*)*'"), fmt("#c3e88d")))
        self._rules.append((re.compile(r'#[^\n]*'),                   fmt("#546e7a")))
        self._rules.append((re.compile(r'\bself\b'),                  fmt("#ff9cac")))

    def highlightBlock(self, text: str) -> None:
        for pattern, fmt in self._rules:
            for m in pattern.finditer(text):
                self.setFormat(m.start(), m.end()-m.start(), fmt)


# ── Panel ─────────────────────────────────────────────────────────────────────

class ScriptEditorPanel(QDockWidget):
    def __init__(self, app, parent=None):
        super().__init__("Script Editor", parent)
        self.app = app
        self._current_path: Optional[Path] = None
        self._modified = False
        self.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.RightDockWidgetArea)

        root = QWidget()
        vbox = QVBoxLayout(root)
        vbox.setContentsMargins(4, 4, 4, 4)
        vbox.setSpacing(4)

        # Toolbar
        toolbar = QHBoxLayout()
        self._file_label = QLabel("(no file open)")
        self._file_label.setStyleSheet("color:#888;font-size:10px;")
        toolbar.addWidget(self._file_label)
        toolbar.addStretch()

        for label, fn in [
            ("New",       self._on_new),
            ("Open…",     self._on_open),
            ("Save",      self._on_save),
            ("Save As…",  self._on_save_as),
            ("▶ Run",     self._on_run),
        ]:
            b = QPushButton(label)
            b.clicked.connect(fn)
            toolbar.addWidget(b)

        vbox.addLayout(toolbar)

        # Split: editor left, transpiled output right (for .amh)
        self._splitter = QSplitter(Qt.Horizontal)

        font = QFont("Consolas,Courier New,monospace", 11)

        self._editor = QPlainTextEdit()
        self._editor.setFont(font)
        self._editor.setLineWrapMode(QPlainTextEdit.NoWrap)
        self._editor.setStyleSheet("background:#1a1a2e;color:#cdd3de;border:none;")
        self._editor.textChanged.connect(self._on_text_changed)
        self._splitter.addWidget(self._editor)

        right = QWidget()
        rvbox = QVBoxLayout(right)
        rvbox.setContentsMargins(0, 0, 0, 0)
        rvbox.addWidget(QLabel("Transpiled Python:"))
        self._transpile_view = QPlainTextEdit()
        self._transpile_view.setFont(font)
        self._transpile_view.setReadOnly(True)
        self._transpile_view.setStyleSheet("background:#0d1117;color:#7ec8e3;border:none;")
        _PyHighlighter(self._transpile_view.document())
        rvbox.addWidget(self._transpile_view)
        self._splitter.addWidget(right)
        self._splitter.setSizes([600, 400])
        self._right_panel = right
        self._right_panel.setVisible(False)

        vbox.addWidget(self._splitter)

        # Status bar
        self._status = QLabel("")
        self._status.setStyleSheet("color:#888;font-size:10px;")
        vbox.addWidget(self._status)

        self.setWidget(root)

        # Auto-transpile timer (debounce 800ms)
        self._transpile_timer = QTimer()
        self._transpile_timer.setSingleShot(True)
        self._transpile_timer.timeout.connect(self._auto_transpile)

    # ------------------------------------------------------------------

    def open_file(self, path: str | Path) -> None:
        p = Path(path)
        if not p.exists():
            return
        self._current_path = p
        self._editor.blockSignals(True)
        self._editor.setPlainText(p.read_text(encoding="utf-8"))
        self._editor.blockSignals(False)

        # Pick highlighter
        if p.suffix == ".amh":
            _AmharicHighlighter(self._editor.document())
            self._right_panel.setVisible(True)
            self._auto_transpile()
        else:
            _PyHighlighter(self._editor.document())
            self._right_panel.setVisible(False)

        self._file_label.setText(str(p))
        self._modified = False
        self._set_status(f"Opened {p.name}")

    # ------------------------------------------------------------------

    def _on_text_changed(self) -> None:
        self._modified = True
        if self._current_path and self._current_path.suffix == ".amh":
            self._transpile_timer.start(800)

    def _auto_transpile(self) -> None:
        src = self._editor.toPlainText()
        from scripting.amharic_transpiler import transpile
        result = transpile(src)
        if result.success:
            self._transpile_view.setPlainText(result.python_src)
            self._set_status("✓ Transpiled OK")
        else:
            self._transpile_view.setPlainText(f"# ── Error ──\n# {result.error}")
            self._set_status(f"✗ {result.error.splitlines()[0][:80]}")

    def _on_new(self) -> None:
        self._current_path = None
        self._editor.clear()
        self._transpile_view.clear()
        self._file_label.setText("(new file)")
        self._modified = False
        default = (
            "ክፍል ስክሪፕት:\n\n"
            "    ተግባር on_start(self):\n"
            "        አትም(\"ሰላም ዓለም!\")\n\n"
            "    ተግባር on_update(self, dt):\n"
            "        ምንም_ሳይሆን\n\n"
            "    ተግባር on_stop(self):\n"
            "        ምንም_ሳይሆን\n"
        )
        self._editor.setPlainText(default)
        _AmharicHighlighter(self._editor.document())
        self._right_panel.setVisible(True)

    def _on_open(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Script",
            str(self.app.project.project_root or ""),
            "Scripts (*.py *.amh);;Python (*.py);;Amharic (*.amh);;All (*)")
        if path:
            self.open_file(path)

    def _on_save(self) -> None:
        if self._current_path:
            self._current_path.write_text(
                self._editor.toPlainText(), encoding="utf-8")
            self._modified = False
            self._set_status(f"Saved {self._current_path.name}")
        else:
            self._on_save_as()

    def _on_save_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Script",
            str(self.app.project.project_root or ""),
            "Amharic Script (*.amh);;Python Script (*.py);;All (*)")
        if path:
            self._current_path = Path(path)
            self._on_save()

    def _on_run(self) -> None:
        """Transpile if .amh and reload the script on the selected entity."""
        if self._current_path:
            self._on_save()

        src = self._editor.toPlainText()
        p   = self._current_path

        if p and p.suffix == ".amh":
            from scripting.amharic_transpiler import transpile
            result = transpile(src)
            if not result.success:
                self._set_status(f"✗ {result.error.splitlines()[0]}")
                self.app.console.error(result.error)
                return
            py_src = result.python_src
        else:
            py_src = src

        # Try to run on the selected entity's ScriptComponent
        e = self.app.selector.selected_entity
        if e:
            from core.script_component import ScriptComponent
            sc = e.get_component(ScriptComponent)
            if sc:
                sc.execute_source(py_src)
                self._set_status(f"▶ Running on '{e.name}'")
                return

        self._set_status("No entity with ScriptComponent selected")

    def _set_status(self, msg: str) -> None:
        self._status.setText(msg)
