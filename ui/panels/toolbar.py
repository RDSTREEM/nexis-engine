from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from ui.theme import (
    ACCENT,
    ACCENT_DIM,
    BG_BASE,
    BORDER,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
    GREEN,
    GREEN_BG,
    GREEN_BORDER,
    VIEWPORT_TOOLBAR_H,
)


def _tool_btn(label: str, tooltip: str = "", checkable: bool = False) -> QPushButton:
    """Small tool button — gizmo toggles, camera mode, etc."""
    btn = QPushButton(label)
    btn.setToolTip(tooltip)
    btn.setCheckable(checkable)
    btn.setStyleSheet(f"""
        QPushButton {{
            background: transparent;
            border: 1px solid transparent;
            border-radius: 4px;
            color: {TEXT_SECONDARY};
            font-size: 11px;
            padding: 3px 8px;
            min-width: 28px;
        }}
        QPushButton:hover {{
            background: #2a2a2a;
            border-color: #3a3a3a;
            color: {TEXT_PRIMARY};
        }}
        QPushButton:pressed {{ background: #222; }}
        QPushButton:checked {{
            background: {ACCENT_DIM};
            border-color: {ACCENT};
            color: {TEXT_PRIMARY};
        }}
        QPushButton:disabled {{ color: #3a3a3a; }}
    """)
    return btn


def _play_btn(label: str, tooltip: str = "") -> QPushButton:
    """Play control button — larger, prominent."""
    btn = QPushButton(label)
    btn.setToolTip(tooltip)
    btn.setFixedWidth(38)
    btn.setStyleSheet(f"""
        QPushButton {{
            background: {GREEN_BG};
            border: 1px solid {GREEN_BORDER};
            border-radius: 4px;
            color: {GREEN};
            font-size: 14px;
            padding: 3px 15px;
            min-width: 35px
        }}
        QPushButton:hover {{ background: #1f3828; border-color: #3a8a4a; }}
        QPushButton:pressed {{ background: #141f18; }}
        QPushButton:disabled {{ color: #2e4a38; background: #141a16; border-color: #1e2e22; }}
    """)
    return btn


def _action_btn(label: str, tooltip: str = "") -> QPushButton:
    """Secondary play action — pause, stop."""
    btn = QPushButton(label)
    btn.setToolTip(tooltip)
    btn.setFixedWidth(34)
    btn.setStyleSheet(f"""
        QPushButton {{
            background: transparent;
            border: 1px solid transparent;
            border-radius: 4px;
            color: {TEXT_SECONDARY};
            font-size: 13px;
            padding: 3px 15px;
            min-width: 35px
        }}
        QPushButton:hover {{
            background: #2a2a2a;
            border-color: #3a3a3a;
            color: {TEXT_PRIMARY};
        }}
        QPushButton:pressed {{ background: #222; }}
        QPushButton:checked {{
            background: {ACCENT_DIM};
            border-color: {ACCENT};
            color: {TEXT_PRIMARY};
        }}
        QPushButton:disabled {{ color: #3a3a3a; }}
    """)
    return btn


def _vline() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.VLine)
    f.setStyleSheet("color: #2a2a2a;")
    f.setFixedWidth(1)
    return f


class ViewportToolbar(QWidget):
    sig_play = Signal()
    sig_pause = Signal()
    sig_stop = Signal()
    sig_cam_toggle = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._viewport = None
        self.setFixedHeight(VIEWPORT_TOOLBAR_H)
        self.setStyleSheet(f"background: {BG_BASE}; border-bottom: 1px solid {BORDER};")

        row = QHBoxLayout(self)
        row.setContentsMargins(10, 0, 10, 0)
        row.setSpacing(4)

        # ── Left: project / scene labels ─────────────────────────────
        self._project_lbl = QLabel("")
        self._project_lbl.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 11px; background: {BG_BASE}; margin-right: 10px"
        )
        row.addWidget(self._project_lbl)

        self._scene_lbl = QLabel("")
        self._scene_lbl.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 11px; background: {BG_BASE}; margin-right: 10px"
        )
        row.addWidget(self._scene_lbl)

        row.addWidget(_vline())

        # ── Camera mode ──────────────────────────────────────────────
        self._2d_btn = _tool_btn("2D", "Orthographic view", checkable=True)
        self._3d_btn = _tool_btn("3D", "Perspective view", checkable=True)
        self._3d_btn.setChecked(True)
        self._2d_btn.clicked.connect(lambda: self._cam_toggle("2d"))
        self._3d_btn.clicked.connect(lambda: self._cam_toggle("3d"))
        row.addWidget(self._2d_btn)
        row.addWidget(self._3d_btn)

        row.addWidget(_vline())

        # ── Gizmo mode ───────────────────────────────────────────────
        self._t_btn = _tool_btn("⇔", "Translate [W]", checkable=True)
        self._r_btn = _tool_btn("↻", "Rotate [E]", checkable=True)
        self._s_btn = _tool_btn("⤡", "Scale [R]", checkable=True)
        self._t_btn.setChecked(True)
        self._t_btn.clicked.connect(lambda: self._gizmo("translate"))
        self._r_btn.clicked.connect(lambda: self._gizmo("rotate"))
        self._s_btn.clicked.connect(lambda: self._gizmo("scale"))
        for b in (self._t_btn, self._r_btn, self._s_btn):
            row.addWidget(b)
        self._gizmo_btns = [self._t_btn, self._r_btn, self._s_btn]

        row.addStretch()

        # ── Centre: play controls ─────────────────────────────────────
        self._play_btn = _play_btn("Play", "Play [Ctrl+P]")
        self._pause_btn = _action_btn("Pause", "Pause [Ctrl+Shift+P]")
        self._stop_btn = _action_btn("Stop", "Stop [Ctrl+Shift+S]")
        self._pause_btn.setCheckable(True)
        self._play_btn.clicked.connect(self.sig_play)
        self._pause_btn.clicked.connect(self.sig_pause)
        self._stop_btn.clicked.connect(self.sig_stop)
        self._play_btn.setEnabled(False)
        self._pause_btn.setEnabled(False)
        self._stop_btn.setEnabled(False)
        for b in (self._play_btn, self._pause_btn, self._stop_btn):
            row.addWidget(b)

        row.addStretch()

        # ── Right: fps counter ────────────────────────────────────────
        self._fps_lbl = QLabel("")
        self._fps_lbl.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 11px; min-width: 60px;"
        )
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
        if not playing:
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
        if self._viewport and hasattr(self._viewport, "gizmo"):
            self._viewport.gizmo.set_mode(mode)
