from __future__ import annotations

from typing import Optional, TYPE_CHECKING
import numpy as np

from core.shader import Shader

if TYPE_CHECKING:
    import moderngl


class Material:
    """
    Holds a Shader plus the uniform values and optional texture
    that define how a surface looks.
    """

    def __init__(self, shader: Optional[Shader] = None, name: str = "Material"):
        self.name: str = name
        self.shader: Shader = shader or Shader.from_builtin("mesh")

        # standard uniforms
        self.color: np.ndarray = np.array([1.0, 1.0, 1.0, 1.0], dtype="f4")
        self.use_texture: bool = False
        self.texture: Optional["moderngl.Texture"] = None

        # default light settings
        self.light_dir: np.ndarray = np.array([0.5, -1.0, 0.5], dtype="f4")
        self.light_color: np.ndarray = np.array([1.0, 1.0, 1.0], dtype="f4")
        self.ambient: float = 0.25

        # arbitrary extra uniforms (name → value)
        self._extras: dict = {}

    # ------------------------------------------------------------------

    def set_color(self, r: float, g: float, b: float, a: float = 1.0) -> None:
        self.color[:] = (r, g, b, a)

    def set_texture(self, texture: "moderngl.Texture") -> None:
        self.texture = texture
        self.use_texture = True

    def set_uniform(self, name: str, value) -> None:
        """Set an arbitrary extra uniform by name."""
        self._extras[name] = value

    def compile(self, ctx: "moderngl.Context") -> None:
        if not self.shader.is_compiled():
            self.shader.compile(ctx)

    def bind(
        self, model_matrix: np.ndarray, view: np.ndarray, proj: np.ndarray
    ) -> None:
        """Write all uniforms into the shader program."""
        prog = self.shader.program
        if prog is None:
            return

        # matrices
        if "u_model" in prog:
            prog["u_model"].write(model_matrix.T.tobytes())
        if "u_view" in prog:
            prog["u_view"].write(view.T.tobytes())
        if "u_proj" in prog:
            prog["u_proj"].write(proj.T.tobytes())

        # material properties
        if "u_color" in prog:
            prog["u_color"].write(self.color.tobytes())
        if "u_use_texture" in prog:
            prog["u_use_texture"].value = self.use_texture
        if "u_light_dir" in prog:
            prog["u_light_dir"].write(self.light_dir.tobytes())
        if "u_light_color" in prog:
            prog["u_light_color"].write(self.light_color.tobytes())
        if "u_ambient" in prog:
            prog["u_ambient"].value = self.ambient

        # texture
        if self.use_texture and self.texture is not None:
            self.texture.use(location=0)
            if "u_texture" in prog:
                prog["u_texture"].value = 0

        # extras
        for name, val in self._extras.items():
            self.shader.set(name, val)

    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "shader": self.shader.to_dict(),
            "color": self.color.tolist(),
            "use_texture": self.use_texture,
            "ambient": self.ambient,
            "light_dir": self.light_dir.tolist(),
            "light_color": self.light_color.tolist(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Material":
        shader = Shader.from_dict(data["shader"])
        mat = cls(shader, name=data.get("name", "Material"))
        mat.color = np.array(data.get("color", [1, 1, 1, 1]), dtype="f4")
        mat.use_texture = data.get("use_texture", False)
        mat.ambient = data.get("ambient", 0.25)
        mat.light_dir = np.array(data.get("light_dir", [0.5, -1, 0.5]), dtype="f4")
        mat.light_color = np.array(data.get("light_color", [1, 1, 1]), dtype="f4")
        return mat

    def __repr__(self) -> str:
        return f"<Material '{self.name}' shader='{self.shader.name}'>"
