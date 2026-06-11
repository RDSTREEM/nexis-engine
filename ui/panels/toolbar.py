"""
toolbar.py — Reworked professional toolbar.
Clean, compact, icon-style buttons with play controls centre-stage.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

_BASE = """
QPushButton {{
    background:{bg};
    border:{border};
    border-radius:4px;
    color:{fg};
    font-size:{fs};
    padding:{pad};
    min-width:{mw};
}}
QPushButton:hover {{ background:{hov}; }}
QPushButton:pressed {{ background:{prs}; }}
QPushButton:checked {{ background:{chk}; border-color:#3c8dde; color:#fff; }}
QPushButton:disabled {{ color:#444; background:#1a1a1a; border-color:#2a2a2a; }}
"""


def _icon_btn(
    label: str, tooltip: str = "", primary: bool = False, checkable: bool = False
) -> QPushButton:
    btn = QPushButton(label)
    btn.setToolTip(tooltip)
    btn.setCheckable(checkable)
    if primary:
        s = _BASE.format(
            bg="#1e3a1e",
            border="1px solid #2d6b2d",
            fg="#55cc55",
            fs="14px",
            pad="3px 12px",
            mw="36px",
            hov="#254a25",
            prs="#162a16",
            chk="#2d6b2d",
        )
    else:
        s = _BASE.format(
            bg="#222",
            border="1px solid #333",
            fg="#bbb",
            fs="11px",
            pad="3px 10px",
            mw="30px",
            hov="#2a2a2a",
            prs="#1a1a1a",
            chk="#1e3a5f",
        )
    btn.setStyleSheet(s)
    return btn


def _vline() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.VLine)
    f.setStyleSheet("color:#2a2a2a;")
    f.setFixedWidth(1)
    return f


class ViewportToolbar(QWidget):
    sig_play = Signal()
    sig_pause = Signal()
    sig_stop = Signal()
    sig_cam_toggle = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._viewport = None  # Set after toolbar is created
        self.setFixedHeight(38)
        self.setStyleSheet("background:#141414;border-bottom:1px solid #1e1e1e;")

        row = QHBoxLayout(self)
        row.setContentsMargins(8, 0, 8, 0)
        row.setSpacing(4)

        # ── Left: scene/project info ─────────────────────────────────
        self._project_lbl = QLabel("")
        self._project_lbl.setStyleSheet("color:#555;font-size:10px;")
        row.addWidget(self._project_lbl)

        self._scene_lbl = QLabel("")
        self._scene_lbl.setStyleSheet("color:#444;font-size:10px;")
        row.addWidget(self._scene_lbl)

        row.addWidget(_vline())

        # ── Camera mode toggle ───────────────────────────────────────
        self._2d_btn = _icon_btn("2D", "Switch to 2D orthographic", checkable=True)
        self._3d_btn = _icon_btn("3D", "Switch to 3D perspective", checkable=True)
        self._3d_btn.setChecked(True)
        self._2d_btn.clicked.connect(lambda: self._cam_toggle("2d"))
        self._3d_btn.clicked.connect(lambda: self._cam_toggle("3d"))
        row.addWidget(self._2d_btn)
        row.addWidget(self._3d_btn)

        row.addWidget(_vline())

        # ── Gizmo mode ───────────────────────────────────────────────
        self._t_btn = _icon_btn("⇔", "Translate [W]", checkable=True)
        self._r_btn = _icon_btn("↻", "Rotate [E]", checkable=True)
        self._s_btn = _icon_btn("⤡", "Scale [R]", checkable=True)
        self._t_btn.setChecked(True)
        self._t_btn.clicked.connect(lambda: self._gizmo("translate"))
        self._r_btn.clicked.connect(lambda: self._gizmo("rotate"))
        self._s_btn.clicked.connect(lambda: self._gizmo("scale"))
        for b in (self._t_btn, self._r_btn, self._s_btn):
            row.addWidget(b)
        self._gizmo_btns = [self._t_btn, self._r_btn, self._s_btn]

        row.addStretch()

        # ── Centre: play controls ────────────────────────────────────
        self._play_btn = _icon_btn("▶", "Play [Ctrl+P]", primary=True)
        self._pause_btn = _icon_btn("⏸", "Pause [Ctrl+Shift+P]")
        self._stop_btn = _icon_btn("⏹", "Stop [Ctrl+Shift+S]")
        self._play_btn.clicked.connect(self.sig_play)
        self._pause_btn.clicked.connect(self.sig_pause)
        self._stop_btn.clicked.connect(self.sig_stop)
        self._play_btn.setEnabled(False)
        self._pause_btn.setEnabled(False)
        self._stop_btn.setEnabled(False)
        for b in (self._play_btn, self._pause_btn, self._stop_btn):
            row.addWidget(b)

        row.addStretch()

        # ── Right: fps counter ───────────────────────────────────────
        self._fps_lbl = QLabel("")
        self._fps_lbl.setStyleSheet("color:#444;font-size:10px;min-width:60px;")
        self._fps_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        row.addWidget(self._fps_lbl)

    # ── Public API ────────────────────────────────────────────────────

    def set_project_type(self, ptype: str) -> None:
        self._project_lbl.setText(f"[{ptype}]")
        if ptype == "2D":
            self._2d_btn.setChecked(True)
            self._3d_btn.setChecked(False)
        else:
            self._3d_btn.setChecked(True)
            self._2d_btn.setChecked(False)

    def set_scene_name(self, name: str) -> None:
        self._scene_lbl.setText(name)

    def enable_play_controls(self, enabled: bool) -> None:
        self._play_btn.setEnabled(enabled)

    def set_playing(self, playing: bool, paused: bool = False) -> None:
        self._play_btn.setEnabled(not playing)
        self._pause_btn.setEnabled(playing)
        self._stop_btn.setEnabled(playing)
        if playing:
            self._play_btn.setStyleSheet(
                self._play_btn.styleSheet().replace(
                    "background:#1e3a1e", "background:#162a16"
                )
            )
        else:
            self._fps_lbl.setText("")

    def set_paused(self, paused: bool) -> None:
        self._pause_btn.setChecked(paused)

    def set_fps(self, fps: float) -> None:
        self._fps_lbl.setText(f"{fps:.0f} fps")

    # ── Internal ──────────────────────────────────────────────────────

    def _cam_toggle(self, mode: str) -> None:
        self._2d_btn.setChecked(mode == "2d")
        self._3d_btn.setChecked(mode == "3d")
        self.sig_cam_toggle.emit(mode)

    def _gizmo(self, mode: str) -> None:
        modes = ["translate", "rotate", "scale"]
        for i, b in enumerate(self._gizmo_btns):
            b.setChecked(modes[i] == mode)
        # forward to viewport gizmo
        if self._viewport and hasattr(self._viewport, "gizmo"):
            self._viewport.gizmo.set_mode(mode)
