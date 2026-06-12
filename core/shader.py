from __future__ import annotations
from pathlib import Path
from typing import Optional

import moderngl

_MESH_VERT = """
#version 330
in vec3 in_position;
in vec3 in_normal;
in vec2 in_uv;

uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_proj;

out vec3 v_normal;
out vec2 v_uv;
out vec3 v_frag_pos;

void main() {
    vec4 world_pos  = u_model * vec4(in_position, 1.0);
    gl_Position     = u_proj * u_view * world_pos;
    v_frag_pos      = world_pos.xyz;
    v_normal        = mat3(transpose(inverse(u_model))) * in_normal;
    v_uv            = in_uv;
}
"""

_MESH_FRAG = """
#version 330
in vec3 v_normal;
in vec2 v_uv;
in vec3 v_frag_pos;

uniform vec4  u_color;
uniform bool  u_use_texture;
uniform sampler2D u_texture;

// simple directional light
uniform vec3  u_light_dir;
uniform vec3  u_light_color;
uniform float u_ambient;

out vec4 f_color;

void main() {
    vec4 base = u_use_texture ? texture(u_texture, v_uv) : u_color;
    vec3 norm = normalize(v_normal);
    float diff = max(dot(norm, normalize(-u_light_dir)), 0.0);
    vec3 lit = base.rgb * (u_ambient + diff * u_light_color);
    f_color = vec4(lit, base.a);
}
"""

_SPRITE_VERT = """
#version 330
in vec2 in_position;
in vec2 in_uv;

uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_proj;

out vec2 v_uv;

void main() {
    gl_Position = u_proj * u_view * u_model * vec4(in_position, 0.0, 1.0);
    v_uv = in_uv;
}
"""

_SPRITE_FRAG = """
#version 330
in vec2 v_uv;

uniform sampler2D u_texture;
uniform vec4      u_color;
uniform bool      u_use_texture;

out vec4 f_color;

void main() {
    if (u_use_texture) {
        f_color = texture(u_texture, v_uv) * u_color;
    } else {
        f_color = u_color;
    }
}
"""

BUILTIN_SHADERS: dict[str, tuple[str, str]] = {
    "mesh": (_MESH_VERT, _MESH_FRAG),
    "sprite": (_SPRITE_VERT, _SPRITE_FRAG),
}


# ------------------------------------------------------------------
# Shader class
# ------------------------------------------------------------------


class Shader:
    """
    Wraps a moderngl Program.
    Can be created from built-in names, raw source strings, or files.
    """

    def __init__(self, name: str = "mesh"):
        self.name = name
        self._vert_src: str = ""
        self._frag_src: str = ""
        self.program: Optional[moderngl.Program] = None

    # -- factory methods --

    @classmethod
    def from_builtin(cls, name: str) -> "Shader":
        if name not in BUILTIN_SHADERS:
            raise ValueError(
                f"Unknown built-in shader '{name}'. "
                f"Available: {list(BUILTIN_SHADERS)}"
            )
        s = cls(name)
        s._vert_src, s._frag_src = BUILTIN_SHADERS[name]
        return s

    @classmethod
    def from_source(cls, vert: str, frag: str, name: str = "custom") -> "Shader":
        s = cls(name)
        s._vert_src = vert
        s._frag_src = frag
        return s

    @classmethod
    def from_files(cls, vert_path: str, frag_path: str) -> "Shader":
        vert = Path(vert_path).read_text(encoding="utf-8")
        frag = Path(frag_path).read_text(encoding="utf-8")
        name = Path(vert_path).stem
        return cls.from_source(vert, frag, name)

    # -- GL compile --

    def compile(self, ctx: moderngl.Context) -> None:
        """Compile shader on the GPU. Must be called after GL context exists."""
        if not self._vert_src or not self._frag_src:
            raise RuntimeError(f"Shader '{self.name}' has no source to compile.")
        self.program = ctx.program(
            vertex_shader=self._vert_src,
            fragment_shader=self._frag_src,
        )

    def is_compiled(self) -> bool:
        return self.program is not None

    # -- uniform helpers --

    def set(self, name: str, value) -> None:
        if self.program and name in self.program:
            (
                self.program[name].write(value)
                if hasattr(value, "tobytes")
                else setattr(self.program[name], "value", value)
            )

    def write(self, name: str, data: bytes) -> None:
        if self.program and name in self.program:
            self.program[name].write(data)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "vert_src": self._vert_src,
            "frag_src": self._frag_src,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Shader":
        if data["name"] in BUILTIN_SHADERS and not data.get("vert_src"):
            return cls.from_builtin(data["name"])
        return cls.from_source(data["vert_src"], data["frag_src"], data["name"])
