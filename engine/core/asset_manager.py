class AssetManager:
    meshes = {}
    materials = {}

    @classmethod
    def register_mesh(cls, name, mesh):
        cls.meshes[name] = mesh

    @classmethod
    def get_mesh(cls, name):
        return cls.meshes.get(name)

    @classmethod
    def register_material(cls, name, material):
        cls.materials[name] = material

    @classmethod
    def get_material(cls, name):
        return cls.materials.get(name)
