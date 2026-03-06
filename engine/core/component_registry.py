class ComponentRegistry:
    _registry = {}

    @classmethod
    def register(cls, name, component_class):
        cls._registry[name] = component_class

    @classmethod
    def get(cls, name):
        return cls._registry.get(name)
