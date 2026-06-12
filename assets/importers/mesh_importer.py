from __future__ import annotations
from pathlib import Path
import numpy as np


def import_mesh(path: Path) -> np.ndarray:
    try:
        import trimesh
    except ImportError:
        raise ImportError("trimesh is required for mesh import: pip install trimesh")

    scene_or_mesh = trimesh.load(str(path), force="mesh")

    # trimesh may return a Scene (multiple meshes) — merge them
    if hasattr(scene_or_mesh, "geometry"):
        import trimesh.util

        mesh = trimesh.util.concatenate(list(scene_or_mesh.geometry.values()))
    else:
        mesh = scene_or_mesh

    mesh.apply_transform(
        trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0])
    )  # flip Y-up → OpenGL convention

    verts = np.array(mesh.vertices, dtype="f4")  # (N,3)
    normals = np.array(mesh.vertex_normals, dtype="f4")  # (N,3)

    if mesh.visual and hasattr(mesh.visual, "uv") and mesh.visual.uv is not None:
        uvs = np.array(mesh.visual.uv, dtype="f4")
    else:
        uvs = np.zeros((len(verts), 2), dtype="f4")

    faces = np.array(mesh.faces, dtype=np.int32)  # (F,3)

    # expand indexed → flat triangle list
    idx = faces.flatten()
    v_flat = verts[idx]
    n_flat = normals[idx]
    uv_flat = uvs[idx]

    data = np.hstack([v_flat, n_flat, uv_flat])  # (F*3, 8)
    return data.astype("f4")
