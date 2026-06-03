from __future__ import annotations
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QFrame
from PySide6.QtCore import Signal


def _vline() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.VLine)
    f.setFrameShadow(QFrame.Sunken)
    return f


class ViewportToolbar(QWidget):
    sig_play = Signal()
    sig_pause = Signal()
    sig_stop = Signal()
    sig_cam_toggle = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(32)
        self.setStyleSheet("background:#1e1e1e;border-bottom:1px solid #333;")

        row = QHBoxLayout(self)
        row.setContentsMargins(8, 0, 8, 0)
        row.setSpacing(6)

        # cam toggle
        self._cam_btn = QPushButton("3D")
        self._cam_btn.setFixedWidth(40)
        self._cam_btn.setCheckable(True)
        self._cam_btn.setToolTip("Toggle editor camera: 3D / 2D ortho")
        self._cam_btn.clicked.connect(self._on_cam_toggle)
        row.addWidget(self._cam_btn)
        row.addWidget(_vline())

        # play controls
        self._play_btn = QPushButton("▶")
        self._pause_btn = QPushButton("⏸")
        self._stop_btn = QPushButton("⏹")
        self._play_btn.setToolTip("Play (Enter play mode)")
        self._pause_btn.setToolTip("Pause / Resume")
        self._stop_btn.setToolTip("Stop (restore scene)")
        for b in (self._play_btn, self._pause_btn, self._stop_btn):
            b.setFixedWidth(32)
            b.setEnabled(False)
            row.addWidget(b)

        self._play_btn.clicked.connect(self.sig_play)
        self._pause_btn.clicked.connect(self.sig_pause)
        self._stop_btn.clicked.connect(self.sig_stop)

        row.addStretch()

        # fps + scene label
        self._fps_lbl = QLabel("")
        self._fps_lbl.setStyleSheet("color:#55aa55;font-size:10px;")
        self._scene_lbl = QLabel("")
        self._scene_lbl.setStyleSheet("color:#888;font-size:11px;")
        row.addWidget(self._fps_lbl)
        row.addWidget(_vline())
        row.addWidget(self._scene_lbl)

    # ------------------------------------------------------------------

    def set_project_type(self, ptype: str) -> None:
        if ptype == "2D":
            self._cam_btn.setVisible(False)
        else:
            self._cam_btn.setVisible(True)
            self._cam_btn.setChecked(False)
            self._cam_btn.setText("3D")

    def set_scene_name(self, name: str) -> None:
        self._scene_lbl.setText(name)

    def set_fps(self, fps: float) -> None:
        self._fps_lbl.setText(f"{fps:.0f} FPS")

    def enable_play_controls(self, enabled: bool) -> None:
        self._play_btn.setEnabled(enabled)
        # pause + stop only enabled when playing
        self._pause_btn.setEnabled(False)
        self._stop_btn.setEnabled(False)

    def set_playing(self, playing: bool, paused: bool) -> None:
        self._play_btn.setEnabled(not playing)
        self._pause_btn.setEnabled(playing)
        self._stop_btn.setEnabled(playing)
        self._cam_btn.setEnabled(not playing)

        # visual indicator — tint window when playing
        if playing and not paused:
            self.setStyleSheet("background:#1a2a1a;border-bottom:1px solid #2a5a2a;")
        elif playing and paused:
            self.setStyleSheet("background:#2a2a1a;border-bottom:1px solid #5a5a2a;")
        else:
            self.setStyleSheet("background:#1e1e1e;border-bottom:1px solid #333;")

    def _on_cam_toggle(self) -> None:
        if self._cam_btn.isChecked():
            self._cam_btn.setText("2D")
            self.sig_cam_toggle.emit("2d")
        else:
            self._cam_btn.setText("3D")
            self.sig_cam_toggle.emit("3d")
