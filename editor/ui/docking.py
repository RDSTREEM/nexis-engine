"""
Docking System for Editor Panels

Provides a docking layout system with:
- Float mode: panels can be moved anywhere freely
- Dock mode: panels snap to edges and can't overlap
- Tab docking: panels can be grouped in tabs
"""

from imgui_bundle import imgui


class DockNode:
    """A node in the docking tree."""

    def __init__(self, panel_id):
        self.panel_id = panel_id
        self.children = []  # Child nodes (for split layouts)
        self.parent = None
        self.size = (0, 0)
        self.position = (0, 0)
        self.is_leaf = True
        self.is_visible = True
        self.dock_position = None  # "left", "right", "top", "bottom", "center"


class PanelState:
    """State for a single panel."""

    def __init__(self, panel_id, title, default_pos, default_size):
        self.panel_id = panel_id
        self.title = title
        self.position = list(default_pos)
        self.size = list(default_size)
        self.is_visible = True
        self.is_floating = False
        self.is_docked = True
        self.dock_target = "center"  # Where panel wants to dock
        self.z_order = 0  # For floating panel z-order


class DockingSystem:
    """
    Manages panel docking layout.

    Modes:
    - Docked: panels are arranged in a grid-like structure
    - Floating: panels can be freely positioned
    """

    def __init__(self, engine):
        self.engine = engine
        self.panels = {}
        self.mode = "docked"  # "docked" or "float"
        self._next_z_order = 1

        # Docking zones (normalized 0-1)
        self.dock_zones = {
            "left": {"x": 0.0, "y": 0.0, "w": 0.2, "h": 1.0},
            "right": {"x": 0.8, "y": 0.0, "w": 0.2, "h": 1.0},
            "top": {"x": 0.0, "y": 0.0, "w": 1.0, "h": 0.1},
            "bottom": {"x": 0.0, "y": 0.9, "w": 1.0, "h": 0.1},
            "center": {"x": 0.2, "y": 0.1, "w": 0.6, "h": 0.8},
        }

    def register_panel(self, panel_id, title, default_pos, default_size):
        """Register a new panel."""
        self.panels[panel_id] = PanelState(panel_id, title, default_pos, default_size)

    def set_panel_mode(self, panel_id, floating):
        """Set a panel to floating or docked mode."""
        if panel_id in self.panels:
            self.panels[panel_id].is_floating = floating
            self.panels[panel_id].is_docked = not floating
            if floating:
                self.panels[panel_id].z_order = self._next_z_order
                self._next_z_order += 1

    def get_top_panel(self):
        """Get the panel with highest z-order."""
        top_panel = None
        max_z = -1
        for panel in self.panels.values():
            if panel.is_floating and panel.z_order > max_z:
                max_z = panel.z_order
                top_panel = panel
        return top_panel

    def begin_docking(self):
        """Begin the docking layout."""
        # Reset all docked panel positions based on mode
        if self.mode == "docked":
            self._layout_docked()
        else:
            self._layout_floating()

    def _layout_docked(self):
        """Layout panels in docked mode."""
        w, h = self.engine.width, self.engine.height

        # Define docked layout regions
        # Left panel: Scene Hierarchy
        left_panel = self.panels.get("scene_hierarchy")
        if left_panel and left_panel.is_visible:
            left_panel.position = [0, 40]
            left_panel.size = [250, h - 40]

        # Right panel: Properties
        right_panel = self.panels.get("properties")
        if right_panel and right_panel.is_visible:
            right_panel.position = [w - 300, 40]
            right_panel.size = [300, h - 40]

        # Bottom panel: Console/Logs
        bottom_panel = self.panels.get("console")
        if bottom_panel and bottom_panel.is_visible:
            bottom_panel.position = [250, h - 150]
            bottom_panel.size = [w - 550, 150]

    def _layout_floating(self):
        """Layout panels in floating mode."""
        # In floating mode, panels keep their last position
        # but can be moved freely
        pass

    def get_panel_rect(self, panel_id):
        """Get the screen rect for a panel."""
        if panel_id in self.panels:
            p = self.panels[panel_id]
            return (
                p.position[0],
                p.position[1],
                p.position[0] + p.size[0],
                p.position[1] + p.size[1],
            )
        return None

    def is_point_in_panel(self, panel_id, x, y):
        """Check if a point is inside a panel."""
        rect = self.get_panel_rect(panel_id)
        if rect:
            return rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3]
        return False

    def find_panel_under_point(self, x, y):
        """Find the panel under a given point (top-most if overlapping)."""
        # Check in z-order for floating panels
        sorted_panels = sorted(
            [p for p in self.panels.values() if p.is_floating],
            key=lambda p: p.z_order,
            reverse=True,
        )

        for panel in sorted_panels:
            if self.is_point_in_panel(panel.panel_id, x, y):
                return panel.panel_id

        # Check docked panels
        for panel in self.panels.values():
            if panel.is_docked and self.is_point_in_panel(panel.panel_id, x, y):
                return panel.panel_id

        return None

    def bring_to_front(self, panel_id):
        """Bring a floating panel to front."""
        if panel_id in self.panels:
            self.panels[panel_id].z_order = self._next_z_order
            self._next_z_order += 1

    def snap_to_dock_zone(self, x, y, width, height):
        """Snap a floating panel to nearest dock zone."""
        center_x = x + width / 2
        center_y = y + height / 2

        # Normalize to 0-1
        norm_x = center_x / self.engine.width
        norm_y = center_y / self.engine.height

        # Find nearest dock zone
        nearest_zone = "center"
        min_dist = float("inf")

        for zone_name, zone in self.dock_zones.items():
            zone_center_x = zone["x"] + zone["w"] / 2
            zone_center_y = zone["y"] + zone["h"] / 2

            dist = (
                (norm_x - zone_center_x) ** 2 + (norm_y - zone_center_y) ** 2
            ) ** 0.5

            if dist < min_dist:
                min_dist = dist
                nearest_zone = zone_name

        return nearest_zone

    def get_dock_position(self, zone):
        """Get the position and size for a panel in a dock zone."""
        w, h = self.engine.width, self.engine.height
        z = self.dock_zones.get(zone, self.dock_zones["center"])

        return (int(z["x"] * w), int(z["y"] * h), int(z["w"] * w), int(z["h"] * h))

    def check_overlap(self, panel_id, x, y, width, height):
        """Check if a panel would overlap with others."""
        for other_id, other in self.panels.items():
            if other_id == panel_id or not other.is_visible:
                continue

            # Check overlap
            if (
                x < other.position[0] + other.size[0]
                and x + width > other.position[0]
                and y < other.position[1] + other.size[1]
                and y + height > other.position[1]
            ):
                return True

        return False

    def find_free_position(self, width, height, start_x=50, start_y=50):
        """Find a non-overlapping position for a new panel."""
        x, y = start_x, start_y
        max_attempts = 100

        for _ in range(max_attempts):
            if not self.check_overlap("new", x, y, width, height):
                return x, y
            x += 20
            if x > self.engine.width - width:
                x = start_x
                y += 20

        return start_x, start_y
