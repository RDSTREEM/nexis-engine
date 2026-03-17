import numpy as np
from engine.components.component import Component
from engine.core.component_registry import ComponentRegistry


class MeshRenderer(Component):
    def __init__(
        self,
        game_object,
        mesh=None,
        material=None,
        mesh_name=None,
        material_name=None,
    ):
        super().__init__(game_object)

        self.mesh = mesh
        self.material = material
        self.mesh_name = mesh_name
        self.material_name = material_name

        self.vao = None

        if self.mesh and self.material:
            self.vao = self.mesh.build_vao(self.material.shader.program)

    def render(self, mvp):
        if not self.vao:
            return

        self.material.shader.set_uniform_matrix("mvp", mvp)
        if hasattr(self.material, "color"):
            self.material.shader.set_uniform_vec4("color", self.material.color)

        self.vao.render()

    def to_dict(self):
        return {
            "type": "MeshRenderer",
            "mesh": self.mesh_name,
            "material": self.material_name,
        }


ComponentRegistry.register("MeshRenderer", MeshRenderer)
