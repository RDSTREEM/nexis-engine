import numpy as np
from engine.components.component import Component
from engine.core.component_registry import ComponentRegistry

class MeshRenderer(Component):
    def __init__(self, game_object, mesh, material):
        super().__init__(game_object)

        self.mesh = mesh
        self.material = material

    def render(self, mvp):
        self.material.shader.set_uniform_matrix("mvp", mvp)
        self.mesh.render()

ComponentRegistry.register("MeshRenderer", MeshRenderer)