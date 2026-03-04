import numpy as np
from engine.components.component import Component
from engine.core.component_registry import ComponentRegistry

class MeshRenderer(Component):
        def __init__(self, game_object, mesh=None, material=None, mesh_name=None, material_name=None):
            super().__init__(game_object)

            self.mesh = mesh
            self.material = material
            self.mesh_name = mesh_name
            self.material_name = material_name    

        def render(self, mvp):
            self.material.shader.set_uniform_matrix("mvp", mvp)
            self.mesh.render()

ComponentRegistry.register("MeshRenderer", MeshRenderer)