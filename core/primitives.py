from __future__ import annotations
import math
import numpy as np


def _vert(pos, nrm, uv) -> list:
    return [*pos, *nrm, *uv]


# ------------------------------------------------------------------
# Cube
# ------------------------------------------------------------------


def cube(size: float = 1.0) -> np.ndarray:
    h = size / 2
    faces = [
        # (positions CCW),  normal
        ([(-h, -h, h), (h, -h, h), (h, h, h), (-h, h, h)], (0, 0, 1)),
        ([(h, -h, -h), (-h, -h, -h), (-h, h, -h), (h, h, -h)], (0, 0, -1)),
        ([(-h, -h, -h), (-h, -h, h), (-h, h, h), (-h, h, -h)], (-1, 0, 0)),
        ([(h, -h, h), (h, -h, -h), (h, h, -h), (h, h, h)], (1, 0, 0)),
        ([(-h, h, h), (h, h, h), (h, h, -h), (-h, h, -h)], (0, 1, 0)),
        ([(-h, -h, -h), (h, -h, -h), (h, -h, h), (-h, -h, h)], (0, -1, 0)),
    ]
    uvs = [(0, 0), (1, 0), (1, 1), (0, 1)]
    tris = [0, 1, 2, 0, 2, 3]
    data = []
    for positions, normal in faces:
        for t in tris:
            data.extend(_vert(positions[t], normal, uvs[t]))
    return np.array(data, dtype="f4")


# ------------------------------------------------------------------
# Plane  (XZ, facing +Y)
# ------------------------------------------------------------------


def plane(size: float = 1.0, subdivisions: int = 1) -> np.ndarray:
    n = subdivisions
    step = size / n
    half = size / 2
    data = []
    for row in range(n):
        for col in range(n):
            x0 = -half + col * step
            x1 = x0 + step
            z0 = -half + row * step
            z1 = z0 + step
            quad = [(x0, 0, z0), (x1, 0, z0), (x1, 0, z1), (x0, 0, z1)]
            uvs = [
                (col / n, row / n),
                ((col + 1) / n, row / n),
                ((col + 1) / n, (row + 1) / n),
                (col / n, (row + 1) / n),
            ]
            nrm = (0, 1, 0)
            for idx in [0, 1, 2, 0, 2, 3]:
                data.extend(_vert(quad[idx], nrm, uvs[idx]))
    return np.array(data, dtype="f4")


# ------------------------------------------------------------------
# Sphere  (UV sphere)
# ------------------------------------------------------------------


def sphere(radius: float = 0.5, stacks: int = 16, slices: int = 16) -> np.ndarray:
    data = []
    for i in range(stacks):
        phi0 = math.pi * i / stacks
        phi1 = math.pi * (i + 1) / stacks
        for j in range(slices):
            theta0 = 2 * math.pi * j / slices
            theta1 = 2 * math.pi * (j + 1) / slices

            def pt(phi, theta):
                x = math.sin(phi) * math.cos(theta)
                y = math.cos(phi)
                z = math.sin(phi) * math.sin(theta)
                return (x * radius, y * radius, z * radius), (x, y, z)

            p00, n00 = pt(phi0, theta0)
            p01, n01 = pt(phi0, theta1)
            p10, n10 = pt(phi1, theta0)
            p11, n11 = pt(phi1, theta1)

            u0, u1 = j / slices, (j + 1) / slices
            v0, v1 = i / stacks, (i + 1) / stacks

            if i != 0:
                data.extend(_vert(p00, n00, (u0, v0)))
                data.extend(_vert(p10, n10, (u0, v1)))
                data.extend(_vert(p11, n11, (u1, v1)))
            if i != stacks - 1:
                data.extend(_vert(p00, n00, (u0, v0)))
                data.extend(_vert(p11, n11, (u1, v1)))
                data.extend(_vert(p01, n01, (u1, v0)))

    return np.array(data, dtype="f4")


# ------------------------------------------------------------------
# Cylinder
# ------------------------------------------------------------------


def cylinder(radius: float = 0.5, height: float = 1.0, slices: int = 16) -> np.ndarray:
    h = height / 2
    data = []
    for i in range(slices):
        a0 = 2 * math.pi * i / slices
        a1 = 2 * math.pi * (i + 1) / slices
        x0, z0 = math.cos(a0), math.sin(a0)
        x1, z1 = math.cos(a1), math.sin(a1)

        # side quad
        pts = [
            (x0 * radius, -h, z0 * radius),
            (x1 * radius, -h, z1 * radius),
            (x1 * radius, h, z1 * radius),
            (x0 * radius, h, z0 * radius),
        ]
        nrm_avg = ((x0 + x1) / 2, 0, (z0 + z1) / 2)
        u0, u1 = i / slices, (i + 1) / slices
        uvs = [(u0, 0), (u1, 0), (u1, 1), (u0, 1)]
        for idx in [0, 1, 2, 0, 2, 3]:
            data.extend(_vert(pts[idx], nrm_avg, uvs[idx]))

        # top cap
        data.extend(_vert((0, h, 0), (0, 1, 0), (0.5, 0.5)))
        data.extend(
            _vert(
                (x1 * radius, h, z1 * radius),
                (0, 1, 0),
                (0.5 + x1 * 0.5, 0.5 + z1 * 0.5),
            )
        )
        data.extend(
            _vert(
                (x0 * radius, h, z0 * radius),
                (0, 1, 0),
                (0.5 + x0 * 0.5, 0.5 + z0 * 0.5),
            )
        )

        # bottom cap
        data.extend(_vert((0, -h, 0), (0, -1, 0), (0.5, 0.5)))
        data.extend(
            _vert(
                (x0 * radius, -h, z0 * radius),
                (0, -1, 0),
                (0.5 + x0 * 0.5, 0.5 + z0 * 0.5),
            )
        )
        data.extend(
            _vert(
                (x1 * radius, -h, z1 * radius),
                (0, -1, 0),
                (0.5 + x1 * 0.5, 0.5 + z1 * 0.5),
            )
        )

    return np.array(data, dtype="f4")


# ------------------------------------------------------------------
# Cone
# ------------------------------------------------------------------


def cone(radius: float = 0.5, height: float = 1.0, slices: int = 16) -> np.ndarray:
    h = height / 2
    data = []
    for i in range(slices):
        a0 = 2 * math.pi * i / slices
        a1 = 2 * math.pi * (i + 1) / slices
        x0, z0 = math.cos(a0) * radius, math.sin(a0) * radius
        x1, z1 = math.cos(a1) * radius, math.sin(a1) * radius

        # side
        nrm = (math.cos((a0 + a1) / 2), 0.5, math.sin((a0 + a1) / 2))
        data.extend(_vert((0, h, 0), nrm, (0.5, 1)))
        data.extend(_vert((x1, -h, z1), nrm, ((i + 1) / slices, 0)))
        data.extend(_vert((x0, -h, z0), nrm, (i / slices, 0)))

        # base cap
        data.extend(_vert((0, -h, 0), (0, -1, 0), (0.5, 0.5)))
        data.extend(
            _vert(
                (x0, -h, z0),
                (0, -1, 0),
                (0.5 + x0 / radius * 0.5, 0.5 + z0 / radius * 0.5),
            )
        )
        data.extend(
            _vert(
                (x1, -h, z1),
                (0, -1, 0),
                (0.5 + x1 / radius * 0.5, 0.5 + z1 / radius * 0.5),
            )
        )

    return np.array(data, dtype="f4")


# ------------------------------------------------------------------
# Capsule  (cylinder + 2 hemisphere caps)
# ------------------------------------------------------------------


def capsule(
    radius: float = 0.5, height: float = 1.0, stacks: int = 8, slices: int = 16
) -> np.ndarray:
    cyl = cylinder(radius, height, slices)
    # top hemisphere
    top = _hemisphere(radius, stacks, slices, top=True, offset_y=height / 2)
    bot = _hemisphere(radius, stacks, slices, top=False, offset_y=-height / 2)
    return np.concatenate([cyl, top, bot])


def _hemisphere(radius, stacks, slices, top: bool, offset_y: float) -> np.ndarray:
    data = []
    sign = 1 if top else -1
    for i in range(stacks):
        phi0 = math.pi / 2 * i / stacks
        phi1 = math.pi / 2 * (i + 1) / stacks
        for j in range(slices):
            theta0 = 2 * math.pi * j / slices
            theta1 = 2 * math.pi * (j + 1) / slices

            def pt(phi, theta):
                x = math.cos(phi) * math.cos(theta)
                y = math.sin(phi) * sign
                z = math.cos(phi) * math.sin(theta)
                return (x * radius, y * radius + offset_y, z * radius), (x, y * sign, z)

            p00, n00 = pt(phi0, theta0)
            p01, n01 = pt(phi0, theta1)
            p10, n10 = pt(phi1, theta0)
            p11, n11 = pt(phi1, theta1)
            u0, u1 = j / slices, (j + 1) / slices
            v0, v1 = i / stacks, (i + 1) / stacks

            if top:
                data.extend(_vert(p00, n00, (u0, v0)))
                data.extend(_vert(p11, n11, (u1, v1)))
                data.extend(_vert(p10, n10, (u0, v1)))
                data.extend(_vert(p00, n00, (u0, v0)))
                data.extend(_vert(p01, n01, (u1, v0)))
                data.extend(_vert(p11, n11, (u1, v1)))
            else:
                data.extend(_vert(p00, n00, (u0, v0)))
                data.extend(_vert(p10, n10, (u0, v1)))
                data.extend(_vert(p11, n11, (u1, v1)))
                data.extend(_vert(p00, n00, (u0, v0)))
                data.extend(_vert(p11, n11, (u1, v1)))
                data.extend(_vert(p01, n01, (u1, v0)))
    return np.array(data, dtype="f4")


# ------------------------------------------------------------------
# Torus
# ------------------------------------------------------------------


def torus(
    major_radius: float = 0.5,
    minor_radius: float = 0.2,
    major_segments: int = 24,
    minor_segments: int = 12,
) -> np.ndarray:
    data = []
    for i in range(major_segments):
        a0 = 2 * math.pi * i / major_segments
        a1 = 2 * math.pi * (i + 1) / major_segments
        for j in range(minor_segments):
            b0 = 2 * math.pi * j / minor_segments
            b1 = 2 * math.pi * (j + 1) / minor_segments

            def pt(a, b):
                cx, cz = math.cos(a) * major_radius, math.sin(a) * major_radius
                nx = math.cos(a) * math.cos(b)
                ny = math.sin(b)
                nz = math.sin(a) * math.cos(b)
                x = cx + math.cos(a) * math.cos(b) * minor_radius
                y = math.sin(b) * minor_radius
                z = cz + math.sin(a) * math.cos(b) * minor_radius
                return (x, y, z), (nx, ny, nz)

            p00, n00 = pt(a0, b0)
            p01, n01 = pt(a0, b1)
            p10, n10 = pt(a1, b0)
            p11, n11 = pt(a1, b1)
            u0, u1 = i / major_segments, (i + 1) / major_segments
            v0, v1 = j / minor_segments, (j + 1) / minor_segments

            data.extend(_vert(p00, n00, (u0, v0)))
            data.extend(_vert(p10, n10, (u1, v0)))
            data.extend(_vert(p11, n11, (u1, v1)))
            data.extend(_vert(p00, n00, (u0, v0)))
            data.extend(_vert(p11, n11, (u1, v1)))
            data.extend(_vert(p01, n01, (u0, v1)))

    return np.array(data, dtype="f4")


# ------------------------------------------------------------------
# Registry  — used by MeshRenderer and asset browser
# ------------------------------------------------------------------

PRIMITIVES: dict[str, callable] = {
    "cube": cube,
    "sphere": sphere,
    "plane": plane,
    "cylinder": cylinder,
    "cone": cone,
    "capsule": capsule,
    "torus": torus,
}


def generate(name: str, **kwargs) -> np.ndarray:
    if name not in PRIMITIVES:
        raise ValueError(f"Unknown primitive '{name}'. Options: {list(PRIMITIVES)}")
    return PRIMITIVES[name](**kwargs)
