"""
primitives_2d.py — Built-in 2D mesh generators.

All functions return a flat float32 numpy array with layout:
  (x, y,  u, v)  — 4 floats per vertex, triangle list.

Coordinates are in world units centered at origin unless noted.
Use with the sprite shader (in_position: vec2, in_uv: vec2).
"""

from __future__ import annotations
import math
import numpy as np


def _quad(x0, y0, x1, y1, u0=0.0, v0=0.0, u1=1.0, v1=1.0) -> list:
    """Two triangles for an axis-aligned quad."""
    return [
        x0,
        y0,
        u0,
        v1,
        x1,
        y0,
        u1,
        v1,
        x1,
        y1,
        u1,
        v0,
        x0,
        y0,
        u0,
        v1,
        x1,
        y1,
        u1,
        v0,
        x0,
        y1,
        u0,
        v0,
    ]


# ------------------------------------------------------------------
# Square  (equal width + height)
# ------------------------------------------------------------------


def square(size: float = 1.0) -> np.ndarray:
    h = size / 2
    return np.array(_quad(-h, -h, h, h), dtype="f4")


# ------------------------------------------------------------------
# Rectangle
# ------------------------------------------------------------------


def rectangle(width: float = 1.0, height: float = 0.5) -> np.ndarray:
    hw, hh = width / 2, height / 2
    return np.array(_quad(-hw, -hh, hw, hh), dtype="f4")


# ------------------------------------------------------------------
# Circle  (triangle fan)
# ------------------------------------------------------------------


def circle(radius: float = 0.5, segments: int = 32) -> np.ndarray:
    data = []
    for i in range(segments):
        a0 = 2 * math.pi * i / segments
        a1 = 2 * math.pi * (i + 1) / segments
        x0, y0 = math.cos(a0) * radius, math.sin(a0) * radius
        x1, y1 = math.cos(a1) * radius, math.sin(a1) * radius
        u0 = 0.5 + math.cos(a0) * 0.5
        v0 = 0.5 - math.sin(a0) * 0.5
        u1 = 0.5 + math.cos(a1) * 0.5
        v1 = 0.5 - math.sin(a1) * 0.5
        # center, p0, p1
        data += [0.0, 0.0, 0.5, 0.5]
        data += [x0, y0, u0, v0]
        data += [x1, y1, u1, v1]
    return np.array(data, dtype="f4")


# ------------------------------------------------------------------
# Triangle  (equilateral, centered)
# ------------------------------------------------------------------


def triangle(size: float = 1.0) -> np.ndarray:
    h = size * math.sqrt(3) / 2
    pts = [
        (0.0, h * 2 / 3),  # top
        (-size / 2, -h / 3),  # bottom-left
        (size / 2, -h / 3),  # bottom-right
    ]
    uvs = [(0.5, 0.0), (0.0, 1.0), (1.0, 1.0)]
    data = []
    for (x, y), (u, v) in zip(pts, uvs):
        data += [x, y, u, v]
    return np.array(data, dtype="f4")


# ------------------------------------------------------------------
# Ellipse
# ------------------------------------------------------------------


def ellipse(width: float = 1.0, height: float = 0.5, segments: int = 32) -> np.ndarray:
    rx, ry = width / 2, height / 2
    data = []
    for i in range(segments):
        a0 = 2 * math.pi * i / segments
        a1 = 2 * math.pi * (i + 1) / segments
        x0, y0 = math.cos(a0) * rx, math.sin(a0) * ry
        x1, y1 = math.cos(a1) * rx, math.sin(a1) * ry
        u0 = 0.5 + math.cos(a0) * 0.5
        v0 = 0.5 - math.sin(a0) * 0.5
        u1 = 0.5 + math.cos(a1) * 0.5
        v1 = 0.5 - math.sin(a1) * 0.5
        data += [0.0, 0.0, 0.5, 0.5]
        data += [x0, y0, u0, v0]
        data += [x1, y1, u1, v1]
    return np.array(data, dtype="f4")


# ------------------------------------------------------------------
# Regular polygon  (triangle=3, square=4, pentagon=5, hexagon=6 …)
# ------------------------------------------------------------------


def regular_polygon(sides: int = 6, radius: float = 0.5) -> np.ndarray:
    if sides < 3:
        raise ValueError("regular_polygon needs at least 3 sides.")
    data = []
    for i in range(sides):
        a0 = 2 * math.pi * i / sides - math.pi / 2
        a1 = 2 * math.pi * (i + 1) / sides - math.pi / 2
        x0, y0 = math.cos(a0) * radius, math.sin(a0) * radius
        x1, y1 = math.cos(a1) * radius, math.sin(a1) * radius
        u0 = 0.5 + math.cos(a0) * 0.5
        v0 = 0.5 - math.sin(a0) * 0.5
        u1 = 0.5 + math.cos(a1) * 0.5
        v1 = 0.5 - math.sin(a1) * 0.5
        data += [0.0, 0.0, 0.5, 0.5]
        data += [x0, y0, u0, v0]
        data += [x1, y1, u1, v1]
    return np.array(data, dtype="f4")


# ------------------------------------------------------------------
# Rounded rectangle
# ------------------------------------------------------------------


def rounded_rect(
    width: float = 1.0,
    height: float = 0.5,
    radius: float = 0.1,
    corner_segments: int = 8,
) -> np.ndarray:
    radius = min(radius, width / 2, height / 2)
    hw, hh = width / 2, height / 2
    ir = radius  # inner radius

    # corner centres
    corners = [
        (hw - ir, hh - ir, 0),  # top-right,    start angle 0
        (-hw + ir, hh - ir, math.pi / 2),  # top-left,     start angle 90
        (-hw + ir, -hh + ir, math.pi),  # bottom-left,  start angle 180
        (hw - ir, -hh + ir, 3 * math.pi / 2),  # bottom-right, start angle 270
    ]

    # build outline vertices (polygon fan from center)
    outline = []
    for cx, cy, start_a in corners:
        for j in range(corner_segments + 1):
            a = start_a + (math.pi / 2) * j / corner_segments
            outline.append((cx + math.cos(a) * ir, cy + math.sin(a) * ir))

    # fan triangulation from centroid
    data = []
    n = len(outline)
    for i in range(n):
        x0, y0 = outline[i]
        x1, y1 = outline[(i + 1) % n]
        u0 = (x0 + hw) / width
        v0 = 1.0 - (y0 + hh) / height
        u1 = (x1 + hw) / width
        v1 = 1.0 - (y1 + hh) / height
        data += [0.0, 0.0, 0.5, 0.5]
        data += [x0, y0, u0, v0]
        data += [x1, y1, u1, v1]
    return np.array(data, dtype="f4")


# ------------------------------------------------------------------
# Nine-slice sprite placeholder  (flat quad, slicing handled in shader)
# ------------------------------------------------------------------


def nine_slice(width: float = 1.0, height: float = 1.0) -> np.ndarray:
    """Simple quad — nine-slice logic is handled via UV shader uniforms."""
    return rectangle(width, height)


# ------------------------------------------------------------------
# Line segment  (thin quad approximation)
# ------------------------------------------------------------------


def line_segment(
    x0: float = -0.5,
    y0: float = 0.0,
    x1: float = 0.5,
    y1: float = 0.0,
    thickness: float = 0.05,
) -> np.ndarray:
    dx = x1 - x0
    dy = y1 - y0
    length = math.sqrt(dx * dx + dy * dy)
    if length < 1e-8:
        return rectangle(0.01, thickness)
    nx = -dy / length * thickness / 2
    ny = dx / length * thickness / 2
    pts = [
        (x0 + nx, y0 + ny),
        (x1 + nx, y1 + ny),
        (x1 - nx, y1 - ny),
        (x0 - nx, y0 - ny),
    ]
    uvs = [(0, 0), (1, 0), (1, 1), (0, 1)]
    data = []
    for idx in [0, 1, 2, 0, 2, 3]:
        x, y = pts[idx]
        u, v = uvs[idx]
        data += [x, y, u, v]
    return np.array(data, dtype="f4")


# ------------------------------------------------------------------
# Tilemap tile  (unit quad, UVs set per-tile by TilemapRenderer)
# ------------------------------------------------------------------


def tile() -> np.ndarray:
    return square(1.0)


# ------------------------------------------------------------------
# Registry
# ------------------------------------------------------------------

PRIMITIVES_2D: dict[str, callable] = {
    "square": square,
    "rectangle": rectangle,
    "circle": circle,
    "triangle": triangle,
    "ellipse": ellipse,
    "regular_polygon": regular_polygon,
    "rounded_rect": rounded_rect,
    "line_segment": line_segment,
    "tile": tile,
}


def generate_2d(name: str, **kwargs) -> np.ndarray:
    if name not in PRIMITIVES_2D:
        raise ValueError(
            f"Unknown 2D primitive '{name}'. Options: {list(PRIMITIVES_2D)}"
        )
    return PRIMITIVES_2D[name](**kwargs)
