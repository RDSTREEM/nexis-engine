class Material:
    def __init__(self, shader, color=(0.2, 0.6, 1.0, 1.0)):
        self.shader = shader
        self.color = color

    def set_color(self, color):
        self.color = color
