"""
theme.py — Single source of truth for all NEXIS UI colors, sizes, and QSS.

Import from here everywhere. Change a value here, it changes everywhere.
"""

# ── Accent ────────────────────────────────────────────────────────────────
ACCENT = "#4a7ddb"  # primary blue — buttons, focus rings, active state
ACCENT_DIM = "#1e3358"  # selection row backgrounds
ACCENT_HOVER = "#5a8de8"  # accent on hover

# ── Backgrounds ───────────────────────────────────────────────────────────
BG_BASE = "#1c1c1c"  # main window / outer shell
BG_SURFACE = "#222222"  # panels, dock backgrounds
BG_RAISED = "#282828"  # inspector cards, card body
BG_HEADER = "#161616"  # all panel toolbars / dock title override
BG_INPUT = "#1a1a1a"  # inputs, spinboxes, text areas
BG_CARD_HDR = "#212121"  # card/section header bars

# ── Borders ───────────────────────────────────────────────────────────────
BORDER = "#2e2e2e"  # default border
BORDER_LIGHT = "#383838"  # input focus, slightly visible
BORDER_ACCENT = ACCENT  # focused inputs

# ── Text ──────────────────────────────────────────────────────────────────
TEXT_PRIMARY = "#e0e0e0"  # main readable text
TEXT_SECONDARY = "#999999"  # labels, secondary info
TEXT_MUTED = "#5a5a5a"  # very low-priority text (timestamps, hints)
TEXT_DISABLED = "#444444"

# ── Semantic ──────────────────────────────────────────────────────────────
GREEN = "#4caf72"  # success / add / play
GREEN_BG = "#1a2e20"
GREEN_BORDER = "#2d6b42"
RED = "#e05555"  # error / delete
RED_BG = "#2a1515"
WARN = "#e0a030"  # warning
WARN_BG = "#2a1f00"

# ── Entity tag colors in hierarchy ────────────────────────────────────────
TAG_GROUP = "#6ab8d4"
TAG_LIGHT = "#e8cb72"
TAG_AUDIO = "#b48ee8"
TAG_DISABLED = "#4a4a4a"

# ── Sizes ─────────────────────────────────────────────────────────────────
PANEL_TOOLBAR_H = 32  # all dock panel inner toolbars
VIEWPORT_TOOLBAR_H = 38  # main viewport toolbar
CARD_HEADER_H = 28  # inspector component card headers
ROW_H = 24  # tree/list row height
FORM_LABEL_W = 88  # inspector form label width


# ── Global QSS ────────────────────────────────────────────────────────────
DARK_QSS = f"""
QMainWindow, QWidget {{
    background: {BG_BASE};
    color: {TEXT_PRIMARY};
    font-size: 12px;
}}

/* ── Menu bar ── */
QMenuBar {{
    background: {BG_HEADER};
    color: {TEXT_SECONDARY};
    border-bottom: 1px solid {BORDER};
    padding: 1px 0;
}}
QMenuBar::item {{
    padding: 4px 10px;
    border-radius: 3px;
}}
QMenuBar::item:selected {{
    background: {BG_RAISED};
    color: {TEXT_PRIMARY};
}}
QMenu {{
    background: {BG_SURFACE};
    border: 1px solid {BORDER_LIGHT};
    border-radius: 6px;
    padding: 4px;
}}
QMenu::item {{
    padding: 5px 14px;
    border-radius: 3px;
    color: {TEXT_PRIMARY};
    font-size: 12px;
}}
QMenu::item:selected {{
    background: {ACCENT_DIM};
    color: {TEXT_PRIMARY};
}}
QMenu::separator {{
    height: 1px;
    background: {BORDER};
    margin: 3px 8px;
}}

/* ── Dock widgets ── */
QDockWidget {{
    border: 1px solid {BORDER};
    titlebar-close-icon: none;
}}
QDockWidget::title {{
    background: {BG_HEADER};
    padding: 4px 8px;
    font-size: 11px;
    font-weight: 600;
    color: {TEXT_SECONDARY};
    border-bottom: 1px solid {BORDER};
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

/* ── Splitter ── */
QSplitter::handle {{
    background: {BORDER};
}}
QSplitter::handle:horizontal {{ width: 1px; }}
QSplitter::handle:vertical {{ height: 1px; }}

/* ── Tree ── */
QTreeWidget {{
    background: {BG_SURFACE};
    border: none;
    color: {TEXT_PRIMARY};
    outline: none;
    alternate-background-color: transparent;
}}
QTreeWidget::item {{
    height: {ROW_H}px;
    padding-left: 2px;
    border-radius: 2px;
}}
QTreeWidget::item:hover {{
    background: {BG_RAISED};
}}
QTreeWidget::item:selected {{
    background: {ACCENT_DIM};
    color: {TEXT_PRIMARY};
}}
QTreeWidget::branch:has-children:closed {{ image: none; }}
QTreeWidget::branch:has-children:open {{ image: none; }}

/* ── List ── */
QListWidget {{
    background: {BG_SURFACE};
    border: none;
    color: {TEXT_PRIMARY};
    outline: none;
}}
QListWidget::item {{
    height: {ROW_H}px;
    padding-left: 4px;
    border-radius: 2px;
}}
QListWidget::item:hover {{ background: {BG_RAISED}; }}
QListWidget::item:selected {{ background: {ACCENT_DIM}; color: {TEXT_PRIMARY}; }}

/* ── Inputs ── */
QDoubleSpinBox, QSpinBox, QLineEdit, QComboBox {{
    background: {BG_INPUT};
    border: 1px solid {BORDER_LIGHT};
    border-radius: 4px;
    padding: 3px 6px;
    color: {TEXT_PRIMARY};
    font-size: 12px;
    selection-background-color: {ACCENT_DIM};
}}
QDoubleSpinBox:focus, QSpinBox:focus, QLineEdit:focus {{
    border-color: {ACCENT};
}}
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button,
QSpinBox::up-button, QSpinBox::down-button {{
    background: {BG_RAISED};
    border: none;
    width: 14px;
}}
QComboBox::drop-down {{
    border: none;
    width: 18px;
}}
QComboBox QAbstractItemView {{
    background: {BG_SURFACE};
    border: 1px solid {BORDER_LIGHT};
    selection-background-color: {ACCENT_DIM};
    color: {TEXT_PRIMARY};
}}

/* ── Buttons ── */
QPushButton {{
    background: {BG_RAISED};
    border: 1px solid {BORDER_LIGHT};
    border-radius: 4px;
    padding: 4px 12px;
    color: {TEXT_PRIMARY};
    font-size: 12px;
}}
QPushButton:hover {{
    background: #323232;
    border-color: #484848;
}}
QPushButton:pressed {{
    background: {BG_SURFACE};
    border-color: {ACCENT};
}}
QPushButton:checked {{
    background: {ACCENT_DIM};
    border-color: {ACCENT};
    color: {TEXT_PRIMARY};
}}
QPushButton:disabled {{
    color: {TEXT_DISABLED};
    background: {BG_SURFACE};
    border-color: {BORDER};
}}

/* ── Checkbox / Label ── */
QCheckBox, QLabel {{
    color: {TEXT_PRIMARY};
    font-size: 12px;
}}
QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    border: 1px solid {BORDER_LIGHT};
    border-radius: 3px;
    background: {BG_INPUT};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
}}

/* ── Scrollbars ── */
QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    border: none;
}}
QScrollBar::handle:vertical {{
    background: #3a3a3a;
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{ background: #4a4a4a; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: transparent;
    height: 6px;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background: #3a3a3a;
    border-radius: 3px;
    min-width: 20px;
}}
QScrollBar::handle:horizontal:hover {{ background: #4a4a4a; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ── Tabs ── */
QTabWidget::pane {{
    border: 1px solid {BORDER};
    background: {BG_SURFACE};
    border-radius: 0 0 4px 4px;
}}
QTabBar::tab {{
    background: {BG_HEADER};
    color: {TEXT_MUTED};
    padding: 5px 14px;
    border: 1px solid {BORDER};
    border-bottom: none;
    font-size: 11px;
}}
QTabBar::tab:selected {{
    background: {BG_SURFACE};
    color: {TEXT_PRIMARY};
    border-bottom-color: {BG_SURFACE};
}}
QTabBar::tab:hover {{
    color: {TEXT_SECONDARY};
}}

/* ── Text editors ── */
QTextEdit, QPlainTextEdit {{
    background: {BG_INPUT};
    color: {TEXT_PRIMARY};
    border: none;
    font-size: 12px;
    selection-background-color: {ACCENT_DIM};
}}

/* ── Dialog ── */
QDialog {{
    background: {BG_SURFACE};
    color: {TEXT_PRIMARY};
}}
QDialogButtonBox QPushButton {{
    min-width: 80px;
    padding: 5px 16px;
}}

/* ── Scroll area ── */
QScrollArea {{
    border: none;
    background: transparent;
}}

/* ── Progress ── */
QProgressBar {{
    background: {BG_INPUT};
    border: 1px solid {BORDER};
    border-radius: 3px;
    height: 6px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background: {ACCENT};
    border-radius: 3px;
}}
"""


def accent_btn_style(bg=ACCENT, hover=ACCENT_HOVER):
    """Return QSS for an accent-colored push button."""
    return (
        f"QPushButton{{background:{bg};border:none;border-radius:4px;"
        f"color:#fff;font-size:12px;font-weight:600;padding:5px 16px;}}"
        f"QPushButton:hover{{background:{hover};}}"
        f"QPushButton:pressed{{background:{ACCENT_DIM};}}"
        f"QPushButton:disabled{{background:#2a2a2a;color:{TEXT_DISABLED};}}"
    )


def green_btn_style():
    """Return QSS for a green 'create/add' push button."""
    return (
        f"QPushButton{{background:{GREEN_BG};border:1px solid {GREEN_BORDER};"
        f"border-radius:4px;color:{GREEN};font-size:12px;padding:4px 12px;}}"
        f"QPushButton:hover{{background:#1f3828;}}"
        f"QPushButton:pressed{{background:#141f18;}}"
    )


def panel_header_style():
    """Return QSS for a panel inner toolbar widget."""
    return f"background:{BG_HEADER};" f"border-bottom:1px solid {BORDER};"
