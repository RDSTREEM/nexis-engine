"""
ModernGL ImGui Renderer

A custom ImGui renderer implementation for ModernGL.
Handles font texture upload, shader management, and draw data rendering.
"""

import numpy as np
import moderngl
from imgui_bundle import imgui


# Vertex shader for ImGui rendering
IMGUI_VERT_SHADER = """#version 330 core

in vec2 position;
in vec2 uv;
in vec4 color;

out vec2 frag_uv;
out vec4 frag_color;

uniform mat4 projection;

void main() {
    frag_uv = uv;
    frag_color = color;
    gl_Position = projection * vec4(position, 0.0, 1.0);
}
"""

# Fragment shader for ImGui rendering
IMGUI_FRAG_SHADER = """#version 330 core

in vec2 frag_uv;
in vec4 frag_color;

out vec4 out_color;

uniform sampler2D texture0;

void main() {
    out_color = frag_color * texture(texture0, frag_uv);
}
"""


class ModernGLImGuiRenderer:
    """
    Custom ImGui renderer for ModernGL.

    Responsibilities:
    - Initialize ImGui font texture and upload to ModernGL texture
    - Create shaders for ImGui rendering
    - Manage VBO/IBO buffers
    - Render ImGui draw_data using ModernGL
    - Handle clip rects via ctx.scissor
    - Enable blending correctly
    """

    def __init__(self, ctx):
        """
        Initialize the ImGui renderer with a ModernGL context.

        Args:
            ctx: ModernGL context
        """
        self.ctx = ctx
        self._font_texture = None
        self._shader = None
        self._vao = None
        self._vbo = None
        self._ibo = None

        # Track OpenGL state for restoration
        # self._prev_blend_enabled = None
        self._prev_blend_func = None
        # self._prev_depth_test_enabled = None
        # self._prev_scissor_enabled = None

        self._initialize()

    def _initialize(self):
        """Initialize shaders, buffers, and font texture."""
        # Create shaders
        self._shader = self.ctx.program(
            vertex_shader=IMGUI_VERT_SHADER,
            fragment_shader=IMGUI_FRAG_SHADER,
        )

        # Create buffers
        self._vbo = self.ctx.buffer(reserve=1000000)
        self._ibo = self.ctx.buffer(reserve=1000000)

        # Create vertex array
        self._vao = self.ctx.vertex_array(
            self._shader,
            [
                (self._vbo, "2f 2f 4f", "position", "uv", "color"),
            ],
            index_buffer=self._ibo,
        )

        # Initialize font texture
        self._create_font_texture()

    def _create_font_texture(self):
        """Create and upload the ImGui font texture."""
        # Get the IO and add default font
        io = imgui.get_io()

        # Add default font using imgui_bundle's API
        font_atlas = io.fonts

        # Build font atlas with default font
        try:
            font_cfg = imgui.ImFontConfig()
            font_cfg.oversample_h = 2
            font_cfg.oversample_v = 1
            self._font = font_atlas.add_font_default(font_cfg)
        except Exception as e:
            # Fallback: create a simple white texture
            self._font = None

        # Get the texture data after building the atlas
        try:
            # Use the correct imgui_bundle API
            tex_width = font_atlas.tex_width
            tex_height = font_atlas.tex_height

            if tex_width == 0 or tex_height == 0:
                # Fallback: create a simple 1x1 white texture
                self._font_texture = self.ctx.texture(
                    (1, 1), 4, bytes([255, 255, 255, 255])
                )
                return

            # Get pixel data as numpy array
            try:
                pixels = font_atlas.tex_pixels_as_rgba32()
            except Exception:
                # Fallback: create a simple white texture
                self._font_texture = self.ctx.texture(
                    (1, 1), 4, bytes([255, 255, 255, 255])
                )
                return

            # Convert to bytes (RGBA format)
            pixel_bytes = pixels.tobytes()

            # Create ModernGL texture
            self._font_texture = self.ctx.texture(
                (tex_width, tex_height), 4, pixel_bytes
            )
            self._font_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
            self._font_texture.repeat_x = False
            self._font_texture.repeat_y = False
        except Exception as e:
            # Fallback: create a simple white texture
            self._font_texture = self.ctx.texture(
                (1, 1), 4, bytes([255, 255, 255, 255])
            )

    @staticmethod
    def unpack_color(c):
        r = (c >> 0) & 255
        g = (c >> 8) & 255
        b = (c >> 16) & 255
        a = (c >> 24) & 255
        return r / 255.0, g / 255.0, b / 255.0, a / 255.0

    def render(self, draw_data):
        if not draw_data:
            return

        # --- Setup GL state (no querying!) ---
        self.ctx.enable(moderngl.BLEND)
        self.ctx.disable(moderngl.DEPTH_TEST)
        # Use raw GL constant for SCISSOR_TEST (0x0C11) - not available in moderngl 5.x
        self.ctx.enable(0x0C11)

        self.ctx.blend_func = (
            moderngl.SRC_ALPHA,
            moderngl.ONE_MINUS_SRC_ALPHA,
        )

        # --- Display size ---
        io = imgui.get_io()
        display_width, display_height = io.display_size

        if display_width <= 0 or display_height <= 0:
            return

        # --- Projection matrix ---
        projection = np.array(
            [
                [2.0 / display_width, 0.0, 0.0, 0.0],
                [0.0, -2.0 / display_height, 0.0, 0.0],
                [0.0, 0.0, -1.0, 0.0],
                [-1.0, 1.0, 0.0, 1.0],
            ],
            dtype="f4",
        )

        self._shader["projection"].write(projection.tobytes())

        # Bind font texture
        self._font_texture.use(0)

        # --- Render draw lists ---
        for draw_list in draw_data.cmd_lists:

            # Upload buffers directly (IMPORTANT FIX)
            vtx_buffer = draw_list.vtx_buffer
            idx_buffer = draw_list.idx_buffer
            vtx_array = np.zeros(
                len(vtx_buffer),
                dtype=[
                    ("position", np.float32, 2),
                    ("uv", np.float32, 2),
                    ("color", np.float32, 4),
                ],
            )

            for i, v in enumerate(vtx_buffer):
                vtx_array["position"][i] = (v.pos.x, v.pos.y)
                vtx_array["uv"][i] = (v.uv.x, v.uv.y)
                vtx_array["color"][i] = self.unpack_color(v.col)

            self._vbo.orphan()
            self._vbo.write(vtx_array.tobytes())

            idx_array = np.array(list(idx_buffer), dtype=np.uint32)
            self._ibo.orphan()
            self._ibo.write(idx_array.tobytes())

            idx_offset = 0

            for cmd in draw_list.cmd_buffer:
                x, y, z, w = cmd.clip_rect

                # Convert to OpenGL coords
                self.ctx.scissor = (
                    int(x),
                    int(display_height - w),
                    int(z - x),
                    int(w - y),
                )

                self._vao.render(
                    mode=moderngl.TRIANGLES,
                    vertices=cmd.elem_count,
                    first=idx_offset,
                )

                idx_offset += cmd.elem_count

        # --- Restore minimal state ---
        self.ctx.disable(0x0C11)  # SCISSOR_TEST
