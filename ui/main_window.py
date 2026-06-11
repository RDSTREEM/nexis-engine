"""
main_window.py
Added: Play in Window button, menu bar hidden on start screen,
       undo/redo refreshes inspector.
"""

from __future__ import annotations
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
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
from ui.panels.scene_list_panel import SceneListPanel

_DARK = """
QMainWindow,QWidget{background:#242424;color:#ddd;}
QMenuBar{background:#1a1a1a;color:#ccc;border-bottom:1px solid #333;}
QMenuBar::item:selected{background:#333;}
QMenu{background:#242424;border:1px solid #3a3a3a;}
QMenu::item:selected{background:#3c8dde;color:#fff;}
QDockWidget{border:1px solid #333;}
QDockWidget::title{background:#1a1a1a;padding:5px 8px;font-size:11px;
                   color:#aaa;border-bottom:1px solid #333;}
QTreeWidget{background:#202020;border:none;color:#ddd;alternate-background-color:#222;}
QTreeWidget::item:selected{background:#3c8dde;color:#fff;}
QTextEdit,QPlainTextEdit{background:#1a1a1a;color:#ccc;border:none;}
QPushButton{background:#333;border:1px solid #484848;border-radius:4px;
            padding:3px 10px;color:#ddd;}
QPushButton:hover{background:#3c3c3c;border-color:#5a5a5a;}
QPushButton:pressed{background:#222;border-color:#666;}
QPushButton:checked{background:#2a4a7a;border-color:#3c8dde;color:#fff;}
QPushButton:disabled{color:#555;background:#2a2a2a;border-color:#333;}
QDoubleSpinBox,QSpinBox,QLineEdit,QComboBox{
    background:#1e1e1e;border:1px solid #3a3a3a;
    border-radius:3px;padding:2px 5px;color:#ddd;}
QDoubleSpinBox:focus,QLineEdit:focus{border-color:#3c8dde;}
QScrollBar:vertical{background:#1e1e1e;width:8px;border:none;}
QScrollBar::handle:vertical{background:#444;border-radius:4px;min-height:24px;}
QScrollBar::handle:vertical:hover{background:#555;}
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}
QCheckBox,QLabel{color:#ddd;}
QTabWidget::pane{border:1px solid #3a3a3a;background:#1e1e1e;}
QTabBar::tab{background:#242424;color:#aaa;padding:5px 12px;
             border:1px solid #3a3a3a;border-bottom:none;}
QTabBar::tab:selected{background:#1e1e1e;color:#ddd;}
QDialog{background:#242424;}
QSplitter::handle{background:#333;}
"""


class MainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setWindowTitle("NEXIS")
        self.resize(1440, 900)
        self.setStyleSheet(_DARK)
        self._play_window = None  # reference kept so it's not GC'd

        self._build_menu()
        self._build_panels()
        self._build_central()

        self.app.console.set_ui_widget(self.console.log_widget())
        self.show_start_screen()

    # ── Menu ─────────────────────────────────────────────────────────────

    def _build_menu(self) -> None:
        mb = self.menuBar()
        mb.setVisible(False)  # hidden until project opens

        fm = mb.addMenu("File")
        self._add_action(fm, "New Project…", "Ctrl+Shift+N", self._on_create)
        self._add_action(fm, "Open Project…", "Ctrl+O", self._on_open)
        self._save_act = self._add_action(fm, "Save", "Ctrl+S", self.app.save_project)
        self._save_act.setEnabled(False)
        fm.addSeparator()
        self._add_action(fm, "Project Settings…", "", lambda: self._open_settings())
        fm.addSeparator()
        self._close_act = self._add_action(
            fm, "Close Project", "", self.app.close_project
        )
        self._close_act.setEnabled(False)

        em = mb.addMenu("Edit")
        self._undo_act = self._add_action(
            em,
            "Undo",
            "Ctrl+Z",
            lambda: (
                self.app.undo.undo(),
                self.hierarchy.refresh(),
                self._refresh_inspector(),
            ),
        )
        self._undo_act.setEnabled(False)
        self._redo_act = self._add_action(
            em,
            "Redo",
            "Ctrl+Y",
            lambda: (
                self.app.undo.redo(),
                self.hierarchy.refresh(),
                self._refresh_inspector(),
            ),
        )
        self._redo_act.setEnabled(False)
        em.addSeparator()
        self._add_action(
            em, "Add Entity", "Ctrl+Shift+A", lambda: self.hierarchy.on_add_entity()
        )
        self._add_action(
            em, "Delete Entity", "Delete", lambda: self.hierarchy.on_delete_entity()
        )

        vm = mb.addMenu("View")
        for label, attr in [
            ("Scene Hierarchy", "hierarchy"),
            ("Inspector", "inspector"),
            ("Console", "console"),
            ("Asset Browser", "asset_browser"),
            ("Script Editor", "script_editor"),
            ("Scenes", "scene_list"),
        ]:
            a = QAction(label, self, checkable=True)
            a.setChecked(True)
            a.triggered.connect(lambda v, x=attr: getattr(self, x).setVisible(v))
            vm.addAction(a)

        pm = mb.addMenu("Play")
        self._add_action(pm, "▶ Play", "Ctrl+P", self._on_play)
        self._add_action(pm, "⏸ Pause", "Ctrl+Shift+P", self._on_pause)
        self._add_action(pm, "⏹ Stop", "Ctrl+Shift+S", self._on_stop)
        pm.addSeparator()
        self._add_action(pm, "▶ Play in Window", "Ctrl+Shift+W", self._on_play_window)

        gm = mb.addMenu("Gizmo")
        self._add_action(
            gm, "Translate (W)", "W", lambda: self.viewport.gizmo.set_mode("translate")
        )
        self._add_action(
            gm, "Rotate (E)", "E", lambda: self.viewport.gizmo.set_mode("rotate")
        )
        self._add_action(
            gm, "Scale (R)", "R", lambda: self.viewport.gizmo.set_mode("scale")
        )

    def _add_action(self, menu, label, shortcut, fn) -> QAction:
        a = QAction(label, self)
        if shortcut:
            a.setShortcut(QKeySequence(shortcut))
        a.triggered.connect(fn)
        menu.addAction(a)
        return a

    def _refresh_inspector(self):
        e = self.app.selector.selected_entity
        if e:
            self.inspector.show_entity(e)
        else:
            self.inspector.clear()

    # ── Panels ───────────────────────────────────────────────────────────

    def _build_panels(self) -> None:
        self.hierarchy = HierarchyPanel(self.app, self)
        self.inspector = InspectorPanel(self.app, self)
        self.console = ConsolePanel(self.app, self)
        self.asset_browser = AssetBrowserPanel(self.app, self)
        self.script_editor = ScriptEditorPanel(self.app, self)
        self.scene_list = SceneListPanel(self.app, self)

        self.addDockWidget(Qt.LeftDockWidgetArea, self.hierarchy)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.scene_list)
        self.addDockWidget(Qt.RightDockWidgetArea, self.inspector)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.console)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.asset_browser)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.script_editor)

        self.tabifyDockWidget(self.hierarchy, self.scene_list)
        self.hierarchy.raise_()
        self.tabifyDockWidget(self.console, self.asset_browser)
        self.tabifyDockWidget(self.asset_browser, self.script_editor)
        self.console.raise_()

        for dock in (
            self.hierarchy,
            self.inspector,
            self.console,
            self.asset_browser,
            self.script_editor,
            self.scene_list,
        ):
            dock.setVisible(False)

    # ── Central ───────────────────────────────────────────────────────────

    def _build_central(self) -> None:
        self.stack = QStackedWidget()

        self.start_screen = StartScreen(
            self.app.console,
            self._on_create,
            self._on_open,
            lambda p: self.app.open_project(p),
        )

        vp_wrap = QWidget()
        vl = QVBoxLayout(vp_wrap)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(0)

        self.toolbar = ViewportToolbar(self)
        self.viewport = ViewportWidget(self.app)
        self.toolbar._viewport = self.viewport  # Set reference for gizmo access

        self.toolbar.sig_cam_toggle.connect(lambda m: self.viewport.camera.set_mode(m))
        self.toolbar.sig_play.connect(self._on_play)
        self.toolbar.sig_pause.connect(self._on_pause)
        self.toolbar.sig_stop.connect(self._on_stop)

        vl.addWidget(self.toolbar)
        vl.addWidget(self.viewport)

        self.stack.addWidget(self.start_screen)
        self.stack.addWidget(vp_wrap)
        self.setCentralWidget(self.stack)

    # ── Visibility ────────────────────────────────────────────────────────

    def _editor_mode(self, on: bool) -> None:
        for dock in (
            self.hierarchy,
            self.inspector,
            self.console,
            self.asset_browser,
            self.script_editor,
            self.scene_list,
        ):
            dock.setVisible(on)
        self._save_act.setEnabled(on)
        self._close_act.setEnabled(on)
        self.menuBar().setVisible(on)
        self.toolbar.enable_play_controls(on)

    def show_start_screen(self) -> None:
        self._editor_mode(False)
        self.stack.setCurrentIndex(0)
        self.start_screen.reload_recent()
        self.setWindowTitle("NEXIS")

    def show_viewport(self) -> None:
        self._editor_mode(True)
        self.stack.setCurrentIndex(1)
        self.setWindowTitle(f"NEXIS — {self.app.project.project_name}")

    # ── Project loaded ────────────────────────────────────────────────────

    def on_project_loaded(self) -> None:
        pt = self.app.project_type
        self.viewport.camera.set_mode("2d" if pt == "2D" else "3d")
        self.toolbar.set_project_type(pt)
        self.toolbar.set_scene_name(
            self.app.active_scene.name if self.app.active_scene else ""
        )
        self.toolbar.enable_play_controls(True)
        self.hierarchy.refresh()
        self.inspector.clear()
        self.asset_browser.refresh()
        self.scene_list.refresh()
        self.show_viewport()

    def refresh_hierarchy(self) -> None:
        self.hierarchy.refresh()

    def _open_settings(self) -> None:
        from ui.panels.settings_panel import open_settings

        open_settings(self.app, self)

    # ── Play ──────────────────────────────────────────────────────────────

    def _on_play(self) -> None:
        self.app.play_mode.play()

    def _on_pause(self) -> None:
        self.app.play_mode.pause()

    def _on_stop(self) -> None:
        self.app.play_mode.stop()

    def _on_play_window(self) -> None:
        """Launch the game in a separate window using game_runner.PlayWindow."""
        proj = self.app.project.project_path
        if proj is None:
            self.app.console.warning("No project open.")
            return
        # Save first so the runner picks up latest changes
        self.app.save_project()
        try:
            from game_runner import PlayWindow

            self._play_window = PlayWindow.launch(str(proj))
            self.app.console.info("Game window opened.")
        except Exception as e:
            self.app.console.error(f"Could not open game window: {e}")

    # ── Dialogs ───────────────────────────────────────────────────────────

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
