from __future__ import annotations
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ui.start_screen import CreateProjectDialog, StartScreen
from ui.viewport import ViewportWidget
from ui.panels.hierarchy_panel import HierarchyPanel
from ui.panels.inspector_panel import InspectorPanel
from ui.panels.console_panel import ConsolePanel
from ui.panels.toolbar import ViewportToolbar
from ui.panels.asset_browser_panel import AssetBrowserPanel
from ui.panels.script_editor_panel import ScriptEditorPanel

_DARK = """
QMainWindow,QWidget{background:#2b2b2b;color:#ddd;}
QMenuBar{background:#1e1e1e;color:#ccc;}
QMenuBar::item:selected{background:#3c3c3c;}
QMenu{background:#2b2b2b;border:1px solid #444;}
QMenu::item:selected{background:#3c8dde;}
QDockWidget::title{background:#1e1e1e;padding:4px;font-size:11px;color:#aaa;}
QTreeWidget{background:#252525;border:none;color:#ddd;}
QTreeWidget::item:selected{background:#3c8dde;color:#fff;}
QTextEdit,QPlainTextEdit{background:#1a1a1a;color:#ccc;border:none;}
QPushButton{background:#3c3c3c;border:1px solid #555;border-radius:3px;padding:3px 8px;color:#ddd;}
QPushButton:hover{background:#4a4a4a;}
QPushButton:pressed{background:#2a2a2a;}
QPushButton:checked{background:#3c8dde;color:#fff;}
QPushButton:disabled{color:#555;}
QDoubleSpinBox,QSpinBox,QLineEdit,QComboBox{background:#1e1e1e;border:1px solid #444;border-radius:2px;padding:2px 4px;color:#ddd;}
QScrollBar:vertical{background:#2b2b2b;width:10px;}
QScrollBar::handle:vertical{background:#555;border-radius:5px;min-height:20px;}
QCheckBox,QLabel{color:#ddd;}
QTabWidget::pane{border:1px solid #444;}
QTabBar::tab{background:#2b2b2b;color:#aaa;padding:4px 10px;border:1px solid #444;}
QTabBar::tab:selected{background:#3c3c3c;color:#ddd;}
"""


class MainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setWindowTitle("NEXIS")
        self.resize(1440, 900)
        self.setStyleSheet(_DARK)

        self._build_menu()
        self._build_panels()
        self._build_central()

        self.app.console.set_ui_widget(self.console.log_widget())
        self.show_start_screen()

    # ------------------------------------------------------------------
    # Menu
    # ------------------------------------------------------------------

    def _build_menu(self) -> None:
        fm = self.menuBar().addMenu("File")
        a = QAction("New Project…", self)
        a.setShortcut("Ctrl+Shift+N")
        a.triggered.connect(self._on_create)
        fm.addAction(a)
        a = QAction("Open Project…", self)
        a.setShortcut("Ctrl+O")
        a.triggered.connect(self._on_open)
        fm.addAction(a)
        self._save_act = QAction("Save", self)
        self._save_act.setShortcut("Ctrl+S")
        self._save_act.setEnabled(False)
        self._save_act.triggered.connect(self.app.save_project)
        fm.addAction(self._save_act)
        fm.addSeparator()
        self._close_act = QAction("Close Project", self)
        self._close_act.setEnabled(False)
        self._close_act.triggered.connect(self.app.close_project)
        fm.addAction(self._close_act)

        em = self.menuBar().addMenu("Edit")
        a = QAction("Add Entity", self)
        a.setShortcut("Ctrl+Shift+A")
        a.triggered.connect(lambda: self.hierarchy.on_add_entity())
        em.addAction(a)
        a = QAction("Delete Entity", self)
        a.setShortcut("Delete")
        a.triggered.connect(lambda: self.hierarchy.on_delete_entity())
        em.addAction(a)

        vm = self.menuBar().addMenu("View")
        for label, attr in [
            ("Scene Hierarchy", "hierarchy"),
            ("Inspector", "inspector"),
            ("Console", "console"),
            ("Asset Browser", "asset_browser"),
            ("Script Editor", "script_editor"),
        ]:
            a = QAction(label, self, checkable=True)
            a.setChecked(True)
            panel_attr = attr
            a.triggered.connect(
                lambda v, pa=panel_attr: getattr(self, pa).setVisible(v)
            )
            vm.addAction(a)

        pm = self.menuBar().addMenu("Play")
        a = QAction("▶ Play", self)
        a.setShortcut("Ctrl+P")
        a.triggered.connect(self._on_play)
        pm.addAction(a)
        a = QAction("⏸ Pause", self)
        a.setShortcut("Ctrl+Shift+P")
        a.triggered.connect(self._on_pause)
        pm.addAction(a)
        a = QAction("⏹ Stop", self)
        a.setShortcut("Ctrl+Shift+S")
        a.triggered.connect(self._on_stop)
        pm.addAction(a)

    # ------------------------------------------------------------------
    # Panels
    # ------------------------------------------------------------------

    def _build_panels(self) -> None:
        self.hierarchy = HierarchyPanel(self.app, self)
        self.inspector = InspectorPanel(self.app, self)
        self.console = ConsolePanel(self.app, self)
        self.asset_browser = AssetBrowserPanel(self.app, self)
        self.script_editor = ScriptEditorPanel(self.app, self)

        self.addDockWidget(Qt.LeftDockWidgetArea, self.hierarchy)
        self.addDockWidget(Qt.RightDockWidgetArea, self.inspector)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.console)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.asset_browser)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.script_editor)

        self.tabifyDockWidget(self.console, self.asset_browser)
        self.tabifyDockWidget(self.asset_browser, self.script_editor)
        self.console.raise_()

        for dock in (
            self.hierarchy,
            self.inspector,
            self.console,
            self.asset_browser,
            self.script_editor,
        ):
            dock.setVisible(False)

    # ------------------------------------------------------------------
    # Central
    # ------------------------------------------------------------------

    def _build_central(self) -> None:
        self.stack = QStackedWidget()

        self.start_screen = StartScreen(
            self.app.console,
            self._on_create,
            self._on_open,
            lambda p: self.app.open_project(p),
        )

        vp_wrap = QWidget()
        vp_lay = QVBoxLayout(vp_wrap)
        vp_lay.setContentsMargins(0, 0, 0, 0)
        vp_lay.setSpacing(0)

        self.toolbar = ViewportToolbar(self)
        self.viewport = ViewportWidget(self.app)

        self.toolbar.sig_cam_toggle.connect(lambda m: self.viewport.camera.set_mode(m))
        self.toolbar.sig_play.connect(self._on_play)
        self.toolbar.sig_pause.connect(self._on_pause)
        self.toolbar.sig_stop.connect(self._on_stop)

        vp_lay.addWidget(self.toolbar)
        vp_lay.addWidget(self.viewport)

        self.stack.addWidget(self.start_screen)
        self.stack.addWidget(vp_wrap)
        self.setCentralWidget(self.stack)

    # ------------------------------------------------------------------
    # Visibility
    # ------------------------------------------------------------------

    def _editor_mode(self, on: bool) -> None:
        for dock in (
            self.hierarchy,
            self.inspector,
            self.console,
            self.asset_browser,
            self.script_editor,
        ):
            dock.setVisible(on)
        self._save_act.setEnabled(on)
        self._close_act.setEnabled(on)

    def show_start_screen(self) -> None:
        self._editor_mode(False)
        self.stack.setCurrentIndex(0)
        self.start_screen.reload_recent()
        self.setWindowTitle("NEXIS")

    def show_viewport(self) -> None:
        self._editor_mode(True)
        self.stack.setCurrentIndex(1)
        self.setWindowTitle(f"NEXIS — {self.app.project.project_name}")

    # ------------------------------------------------------------------
    # Project loaded
    # ------------------------------------------------------------------

    def on_project_loaded(self) -> None:
        pt = self.app.project_type
        cam = self.viewport.camera
        cam.set_mode("2d" if pt == "2D" else "3d")
        self.toolbar.set_project_type(pt)
        self.toolbar.set_scene_name(
            self.app.active_scene.name if self.app.active_scene else ""
        )
        self.toolbar.enable_play_controls(True)
        self.hierarchy.refresh()
        self.inspector.clear()
        self.asset_browser.refresh()
        self.show_viewport()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def refresh_hierarchy(self) -> None:
        self.hierarchy.refresh()

    # ------------------------------------------------------------------
    # Play signals
    # ------------------------------------------------------------------

    def _on_play(self) -> None:
        self.app.play_mode.play()

    def _on_pause(self) -> None:
        self.app.play_mode.pause()

    def _on_stop(self) -> None:
        self.app.play_mode.stop()

    # ------------------------------------------------------------------
    # Dialogs
    # ------------------------------------------------------------------

    def _on_create(self) -> None:
        dlg = CreateProjectDialog(self)
        if dlg.exec() == QDialog.Accepted:
            folder, name, ptype = dlg.result_data()
            if folder and name:
                self.app.create_project(Path(folder), name, ptype)

    def _on_open(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Project",
            str(Path.home()),
            "NEXIS Project (*.nexis);;All Files (*)",
        )
        if path:
            self.app.open_project(path)
