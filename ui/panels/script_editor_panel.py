"""
script_editor_panel.py
In-engine script editor with syntax highlighting.
Opens .py and .amh files, saves on Ctrl+S, triggers hot-reload.
"""

from __future__ import annotations
from pathlib import Path

from PySide6.QtCore import Qt, QRegularExpression
from PySide6.QtGui import (
    QColor,
    QFont,
    QSyntaxHighlighter,
    QTextCharFormat,
    QKeySequence,
)
from PySide6.QtWidgets import (
    QDockWidget,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QShortcut,
)

# ------------------------------------------------------------------
# Syntax highlighter (Python + Amharic keywords)
# ------------------------------------------------------------------


class _Highlighter(QSyntaxHighlighter):
    def __init__(self, doc):
        super().__init__(doc)
        self._rules: list[tuple] = []

        def _fmt(color, bold=False, italic=False):
            f = QTextCharFormat()
            f.setForeground(QColor(color))
            if bold:
                f.setFontWeight(700)
            if italic:
                f.setFontItalic(True)
            return f

        kw_fmt = _fmt("#cc99cd", bold=True)
        amh_fmt = _fmt("#e8a87c", bold=True)
        str_fmt = _fmt("#7ec699")
        num_fmt = _fmt("#f08d49")
        cmt_fmt = _fmt("#666666", italic=True)
        fn_fmt = _fmt("#6cb6ff")
        self_fmt = _fmt("#e06c75")
        dec_fmt = _fmt("#61afef")

        py_kw = (
            r"\b(def|class|return|if|elif|else|while|for|in|import|from|as|"
            r"try|except|finally|raise|global|nonlocal|pass|break|continue|"
            r"True|False|None|and|or|not|with|yield|lambda|assert|del|"
            r"print|len|range|int|float|str|bool|list|dict|tuple|set)\b"
        )
        amh_kw = (
            r"\b(ክፍል|ተግባር|ካርታ|ከሆነ|ካልሆነ|እስካለ|ለእያንዳንዱ|ውስጥ|"
            r"እውነት|ሐሰት|ምንም|አትም|እና|ወይም|አይደለም|አቁም|ቀጥል)\b"
        )

        rules = [
            (py_kw, kw_fmt),
            (amh_kw, amh_fmt),
            (r'"[^"\\]*(\\.[^"\\]*)*"', str_fmt),
            (r"'[^'\\]*(\\.[^'\\]*)*'", str_fmt),
            (r"\b\d+\.?\d*\b", num_fmt),
            (r"#[^\n]*", cmt_fmt),
            (r"\bdef\s+(\w+)", fn_fmt),
            (r"\bself\b", self_fmt),
            (r"@\w+", dec_fmt),
        ]
        for pattern, fmt in rules:
            self._rules.append((QRegularExpression(pattern), fmt))

    def highlightBlock(self, text: str) -> None:
        for rx, fmt in self._rules:
            it = rx.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)


# ------------------------------------------------------------------
# Panel
# ------------------------------------------------------------------


class ScriptEditorPanel(QDockWidget):
    def __init__(self, app, parent=None):
        super().__init__("Script Editor", parent)
        self.app = app
        self._current_path: str = ""
        self.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.RightDockWidgetArea)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # toolbar
        bar = QWidget()
        bar.setFixedHeight(28)
        bar.setStyleSheet("background:#1a1a1a;")
        bar_row = QHBoxLayout(bar)
        bar_row.setContentsMargins(6, 0, 6, 0)
        bar_row.setSpacing(6)

        self._path_lbl = QLabel("No file open")
        self._path_lbl.setStyleSheet("color:#888;font-size:10px;")
        bar_row.addWidget(self._path_lbl)
        bar_row.addStretch()

        open_btn = QPushButton("Open…")
        open_btn.setFixedHeight(22)
        save_btn = QPushButton("Save")
        save_btn.setFixedHeight(22)
        new_btn = QPushButton("New")
        new_btn.setFixedHeight(22)
        open_btn.clicked.connect(self._on_open)
        save_btn.clicked.connect(self._on_save)
        new_btn.clicked.connect(self._on_new)
        for b in (new_btn, open_btn, save_btn):
            bar_row.addWidget(b)

        layout.addWidget(bar)

        # editor
        self._editor = QPlainTextEdit()
        self._editor.setFont(QFont("Consolas", 10))
        self._editor.setStyleSheet("background:#1a1a1a;color:#abb2bf;border:none;")
        self._editor.setTabStopDistance(28)
        self._hl = _Highlighter(self._editor.document())
        layout.addWidget(self._editor)

        self.setWidget(container)

        # Ctrl+S shortcut
        sc = QShortcut(QKeySequence("Ctrl+S"), self._editor)
        sc.activated.connect(self._on_save)

    # ------------------------------------------------------------------

    def open_file(self, path: str) -> None:
        try:
            self._editor.setPlainText(Path(path).read_text(encoding="utf-8"))
            self._current_path = path
            self._path_lbl.setText(Path(path).name)
            self.raise_()
        except Exception as e:
            self.app.console.warning(f"Script editor: could not open {path}: {e}")

    def _on_open(self) -> None:
        p, _ = QFileDialog.getOpenFileName(
            self,
            "Open Script",
            str(self.app.project.project_root or Path.home()),
            "Scripts (*.py *.amh);;All Files (*)",
        )
        if p:
            self.open_file(p)

    def _on_save(self) -> None:
        if not self._current_path:
            p, _ = QFileDialog.getSaveFileName(
                self,
                "Save Script",
                str(self.app.project.project_root or Path.home()),
                "Python (*.py);;Amharic (*.amh)",
            )
            if not p:
                return
            self._current_path = p
            self._path_lbl.setText(Path(p).name)
        try:
            Path(self._current_path).write_text(
                self._editor.toPlainText(), encoding="utf-8"
            )
            self.app.console.info(f"Saved: {Path(self._current_path).name}")
        except Exception as e:
            self.app.console.warning(f"Save failed: {e}")

    def _on_new(self) -> None:
        template = (
            "class Script:\n"
            "    def on_start(self, entity):\n"
            "        pass\n\n"
            "    def on_update(self, entity, dt):\n"
            "        pass\n\n"
            "    def on_stop(self, entity):\n"
            "        pass\n\n"
            "    def on_input(self, entity, key, pressed):\n"
            "        pass\n"
        )
        self._editor.setPlainText(template)
        self._current_path = ""
        self._path_lbl.setText("Untitled")
