from __future__ import annotations
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import (
    QColor,
    QFont,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextDocument,
)
from PySide6.QtWidgets import (
    QDockWidget,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

_FONT = QFont("Consolas", 11)
_FONT.setStyleHint(QFont.Monospace)


def _fmt(colour: str, bold: bool = False) -> QTextCharFormat:
    f = QTextCharFormat()
    f.setForeground(QColor(colour))
    if bold:
        f.setFontWeight(700)
    return f


_AMH_KW = _fmt("#c792ea", bold=True)  # purple — Amharic language keywords
_PY_KW = _fmt("#82aaff", bold=True)  # blue   — Python keywords (allowed too)
_API_KW = _fmt("#ffcb6b", bold=True)  # gold   — engine API names
_NUMBER = _fmt("#f78c6c")  # orange
_STRING = _fmt("#c3e88d")  # green
_COMMENT = _fmt("#546e7a")  # grey
_SELF = _fmt("#ff9cac")  # pink  — ራስ / self
_FUNC_NM = _fmt("#82aaff")  # blue  — function names
_BOOL = _fmt("#f07178")  # red   — እውነት/ሐሰት/ምንም


class _AmharicHighlighter(QSyntaxHighlighter):
    def __init__(self, doc: QTextDocument):
        super().__init__(doc)
        import re
        from scripting.amharic_transpiler import get_amharic_keywords

        all_kws = get_amharic_keywords()
        from scripting.amharic_transpiler import (
            _KEYWORDS,
            _IDENTIFIER_MAP,
            _CLASS_NAME_MAP,
        )

        amh_lang = [k for k, _ in _KEYWORDS]
        amh_api = [k for k in _IDENTIFIER_MAP if k not in ("ራስ",) and k not in amh_lang]
        amh_bool = ["እውነት", "ሐሰት", "ምንም"]
        py_kws = [
            "def",
            "class",
            "if",
            "elif",
            "else",
            "while",
            "for",
            "in",
            "return",
            "break",
            "continue",
            "pass",
            "and",
            "or",
            "not",
            "True",
            "False",
            "None",
            "import",
            "from",
            "as",
            "try",
            "except",
            "finally",
            "raise",
            "global",
            "print",
            "self",
        ]

        self._rules: list = []

        # Comments first (highest priority)
        self._rules.append((re.compile(r"#[^\n]*"), _COMMENT))

        # Strings
        self._rules.append((re.compile(r'"[^"\\]*(?:\\.[^"\\]*)*"'), _STRING))
        self._rules.append((re.compile(r"'[^'\\]*(?:\\.[^'\\]*)*'"), _STRING))

        # Booleans / None
        for kw in amh_bool:
            self._rules.append((re.compile(rf"(?<!\w){re.escape(kw)}(?!\w)"), _BOOL))

        # ራስ (self equivalent)
        self._rules.append((re.compile(r"(?<!\w)ራስ(?!\w)"), _SELF))
        self._rules.append((re.compile(r"(?<!\w)self(?!\w)"), _SELF))

        # Engine API identifiers
        for kw in sorted(amh_api, key=len, reverse=True):
            self._rules.append((re.compile(rf"(?<!\w){re.escape(kw)}(?!\w)"), _API_KW))

        # Amharic language keywords
        for kw in sorted(amh_lang, key=len, reverse=True):
            self._rules.append((re.compile(rf"(?<!\w){re.escape(kw)}(?!\w)"), _AMH_KW))

        # Python keywords (allowed as fallback)
        for kw in py_kws:
            self._rules.append((re.compile(rf"\b{kw}\b"), _PY_KW))

        # Numbers
        self._rules.append((re.compile(r"\b\d+(\.\d+)?\b"), _NUMBER))

        # Function/class name after ተግባር/ክፍል/def/class
        self._rules.append(
            (
                re.compile(
                    r"(?:ተግባር|ክፍል|def|class)\s+"
                    r"([A-Za-z_\u1200-\u137F\u1380-\u139F][A-Za-z0-9_\u1200-\u137F\u1380-\u139F]*)"
                ),
                _FUNC_NM,
            )
        )

    def highlightBlock(self, text: str) -> None:
        for pat, fmt in self._rules:
            for m in pat.finditer(text):
                self.setFormat(m.start(), m.end() - m.start(), fmt)


class _PyHighlighter(QSyntaxHighlighter):
    def __init__(self, doc: QTextDocument):
        super().__init__(doc)
        import re

        kws = [
            "def",
            "class",
            "if",
            "elif",
            "else",
            "while",
            "for",
            "in",
            "return",
            "break",
            "continue",
            "pass",
            "and",
            "or",
            "not",
            "True",
            "False",
            "None",
            "import",
            "from",
            "as",
            "try",
            "except",
            "finally",
            "raise",
            "global",
            "print",
        ]
        self._rules = []
        self._rules.append((re.compile(r"#[^\n]*"), _COMMENT))
        self._rules.append((re.compile(r'"[^"\\]*(?:\\.[^"\\]*)*"'), _STRING))
        self._rules.append((re.compile(r"'[^'\\]*(?:\\.[^'\\]*)*'"), _STRING))
        self._rules.append((re.compile(r"(?<!\w)self(?!\w)"), _SELF))
        for kw in kws:
            self._rules.append((re.compile(rf"\b{kw}\b"), _PY_KW))
        self._rules.append((re.compile(r"\b\d+(\.\d+)?\b"), _NUMBER))

    def highlightBlock(self, text: str) -> None:
        for pat, fmt in self._rules:
            for m in pat.finditer(text):
                self.setFormat(m.start(), m.end() - m.start(), fmt)


# ── Default new-file templates ─────────────────────────────────────────────
_NEW_AMH = """\
# ስክሪፕት.amh — አዲስ ስክሪፕት

ክፍል ስክሪፕት:

    ተግባር ሲጀምር(ራስ, ነፍስ):
        አትም("ሰላም ዓለም!")

    ተግባር ሲዘምን(ራስ, ነፍስ, dt):
        ምንም_ሳይሆን

    ተግባር ሲቆም(ራስ, ነፍስ):
        ምንም_ሳይሆን

    ተግባር ሲገቡ(ራስ, ነፍስ, ቁልፍ, ተጫነ):
        ምንም_ሳይሆን
"""

_NEW_PY = """\
# script.py

class Script:

    def on_start(self, entity):
        print("Hello!")

    def on_update(self, entity, dt):
        pass

    def on_stop(self, entity):
        pass

    def on_input(self, entity, key, pressed):
        pass
"""


# ── Panel ──────────────────────────────────────────────────────────────────
class ScriptEditorPanel(QDockWidget):
    def __init__(self, app, parent=None):
        super().__init__("Script Editor", parent)
        self.app = app
        self._path: Optional[Path] = None
        self._modified = False
        self.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.RightDockWidgetArea)

        root = QWidget()
        vbox = QVBoxLayout(root)
        vbox.setContentsMargins(4, 4, 4, 4)
        vbox.setSpacing(3)
        self.setWidget(root)

        # ── toolbar ───────────────────────────────────────────────────
        tbar = QHBoxLayout()
        self._file_lbl = QLabel("(no file)")
        self._file_lbl.setStyleSheet("color:#666; font-size:10px;")
        tbar.addWidget(self._file_lbl, 1)

        btn_style = (
            "QPushButton{background:#2a2a2a;border:1px solid #3a3a3a;"
            "border-radius:3px;color:#ccc;padding:2px 8px;font-size:10px;}"
            "QPushButton:hover{background:#333;}"
        )
        for lbl, fn in [
            ("New .amh", self._new_amh),
            ("New .py", self._new_py),
            ("Open…", self._open),
            ("Save", self._save),
            ("▶ Run", self._run),
        ]:
            b = QPushButton(lbl)
            b.setStyleSheet(btn_style)
            b.clicked.connect(fn)
            tbar.addWidget(b)
        vbox.addLayout(tbar)

        # ── split: editor | transpile output ─────────────────────────
        self._split = QSplitter(Qt.Horizontal)

        self._editor = QPlainTextEdit()
        self._editor.setFont(_FONT)
        self._editor.setLineWrapMode(QPlainTextEdit.NoWrap)
        self._editor.setStyleSheet(
            "QPlainTextEdit{background:#1a1a2e;color:#cdd3de;"
            "border:none;selection-background-color:#2d4a7a;}"
        )
        self._editor.textChanged.connect(self._on_changed)
        self._split.addWidget(self._editor)

        # right pane — only visible for .amh
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.setSpacing(2)
        lbl = QLabel("Transpiled Python")
        lbl.setStyleSheet("color:#555;font-size:10px;padding:2px 4px;")
        rv.addWidget(lbl)
        self._out = QPlainTextEdit()
        self._out.setFont(_FONT)
        self._out.setReadOnly(True)
        self._out.setStyleSheet(
            "QPlainTextEdit{background:#0d1117;color:#5aadce;" "border:none;}"
        )
        _PyHighlighter(self._out.document())
        rv.addWidget(self._out)
        self._right = right
        self._right.setVisible(False)
        self._split.addWidget(right)
        self._split.setSizes([600, 400])

        vbox.addWidget(self._split, 1)

        # status
        self._status = QLabel("")
        self._status.setStyleSheet("color:#666;font-size:9px;padding:1px 4px;")
        vbox.addWidget(self._status)

        # debounce timer for live transpile
        self._tp_timer = QTimer()
        self._tp_timer.setSingleShot(True)
        self._tp_timer.timeout.connect(self._transpile_preview)

    # ── Public ────────────────────────────────────────────────────────

    def open_file(self, path: str | Path) -> None:
        p = Path(path)
        if not p.exists():
            return
        self._path = p
        self._editor.blockSignals(True)
        self._editor.setPlainText(p.read_text(encoding="utf-8"))
        self._editor.blockSignals(False)
        self._apply_highlighter()
        self._modified = False
        self._file_lbl.setText(p.name)
        self._status_ok(f"Opened {p.name}")
        if p.suffix == ".amh":
            self._transpile_preview()

    # ── Toolbar actions ───────────────────────────────────────────────

    def _new_amh(self):
        self._path = None
        self._editor.setPlainText(_NEW_AMH)
        _AmharicHighlighter(self._editor.document())
        self._right.setVisible(True)
        self._file_lbl.setText("new file.amh")
        self._transpile_preview()

    def _new_py(self):
        self._path = None
        self._editor.setPlainText(_NEW_PY)
        _PyHighlighter(self._editor.document())
        self._right.setVisible(False)
        self._file_lbl.setText("new file.py")

    def _open(self):
        p, _ = QFileDialog.getOpenFileName(
            self,
            "Open Script",
            str(getattr(self.app.project, "project_root", "") or ""),
            "Scripts (*.py *.amh);;Amharic (*.amh);;Python (*.py);;All (*)",
        )
        if p:
            self.open_file(p)

    def _save(self):
        if self._path is None:
            suffix = ".amh" if self._right.isVisible() else ".py"
            p, _ = QFileDialog.getSaveFileName(
                self,
                "Save Script",
                str(getattr(self.app.project, "project_root", "") or ""),
                f"Script (*{suffix});;All (*)",
            )
            if not p:
                return
            self._path = Path(p)
        self._path.write_text(self._editor.toPlainText(), encoding="utf-8")
        self._modified = False
        self._file_lbl.setText(self._path.name)
        self._status_ok(f"Saved {self._path.name}")

    def _run(self):
        if self._path:
            self._save()
        src = self._editor.toPlainText()
        is_amh = (
            self._path and self._path.suffix == ".amh"
            if self._path
            else self._right.isVisible()
        )
        if is_amh:
            from scripting.amharic_transpiler import transpile

            py_src = transpile(src)
        else:
            py_src = src

        e = self.app.selector.selected_entity
        if e:
            from core.script_component import ScriptComponent

            sc = e.get_component(ScriptComponent)
            if sc:
                sc.execute_source(py_src)
                self._status_ok(f"Running on '{e.name}'")
                return
        self._status_err("Select an entity with a ScriptComponent first")

    # ── Internal ──────────────────────────────────────────────────────

    def _on_changed(self):
        self._modified = True
        if self._right.isVisible():
            self._tp_timer.start(700)

    def _apply_highlighter(self):
        if self._path and self._path.suffix == ".amh":
            _AmharicHighlighter(self._editor.document())
            self._right.setVisible(True)
        else:
            _PyHighlighter(self._editor.document())
            self._right.setVisible(False)

    def _transpile_preview(self):
        src = self._editor.toPlainText()
        from scripting.amharic_transpiler import transpile

        try:
            py = transpile(src)
            self._out.setPlainText(py)
            self._status_ok("✓ Transpile OK")
        except Exception as e:
            self._out.setPlainText(f"# Error\n# {e}")
            self._status_err(str(e)[:100])

    def _status_ok(self, msg: str):
        self._status.setText(msg)
        self._status.setStyleSheet("color:#5a5;font-size:9px;padding:1px 4px;")

    def _status_err(self, msg: str):
        self._status.setText(msg)
        self._status.setStyleSheet("color:#f55;font-size:9px;padding:1px 4px;")
