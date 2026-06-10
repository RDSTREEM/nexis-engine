"""
scene_loader.py
Post-load texture restoration.
Call `restore_textures(scene, ctx)` after loading a scene from disk
so materials with a saved tex_path re-upload their texture to GPU.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import moderngl
    from core.scene import Scene


def restore_textures(scene: "Scene", ctx: "moderngl.Context") -> None:
    """
    Walk every renderer in the scene and call material.reload_texture(ctx)
    for any material that has a saved _tex_path but no live GPU texture.
    Called once after scene.from_dict() + GL context is ready.
    """
    from core.mesh_renderer   import MeshRenderer
    from core.sprite_renderer import SpriteRenderer

    for entity in scene.all_entities():
        for comp_cls in (MeshRenderer, SpriteRenderer):
            comp = entity.get_component(comp_cls)
            if comp and hasattr(comp, "material") and comp.material:
                mat = comp.material
                if mat._tex_path and not mat.texture:
                    ok = mat.reload_texture(ctx)
                    if ok:
                        comp._vao = None   # force VAO rebuild
