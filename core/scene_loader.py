from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import moderngl
    from core.scene import Scene


def restore_textures(scene: "Scene", ctx: "moderngl.Context") -> None:
    from core.mesh_renderer import MeshRenderer
    from core.sprite_renderer import SpriteRenderer

    for entity in scene.all_entities():
        for comp_cls in (MeshRenderer, SpriteRenderer):
            comp = entity.get_component(comp_cls)
            if comp and hasattr(comp, "material") and comp.material:
                mat = comp.material
                if mat._tex_path and not mat.texture:
                    ok = mat.reload_texture(ctx)
                    if ok:
                        comp._vao = None  # force VAO rebuild
