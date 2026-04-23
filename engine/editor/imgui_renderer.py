"""
ModernGL ImGui Renderer

A custom ImGui renderer implementation for ModernGL.
Handles font texture upload, shader management, and draw data rendering.
"""

import numpy as np
import struct
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
        self._prev_blend_enabled = None
        self._prev_blend_func = None
        self._prev_depth_test_enabled = None
        self._prev_scissor_enabled = None

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
            font_atlas.add_font_default(font_cfg)
        except Exception as e:
            # Fallback: create a simple white texture
            pass

        # Get the texture data after building the atlas
        tex_data = font_atlas.tex_data

        if tex_data is None or tex_data.width == 0:
            # Fallback: create a simple 1x1 white texture
            self._font_texture = self.ctx.texture(
                (1, 1), 4, bytes([255, 255, 255, 255])
            )
            return

        # Get pixel data as numpy array
        pixels = tex_data.get_pixels_array()
        width = tex_data.width
        height = tex_data.height
        bpp = tex_data.bytes_per_pixel

        # Convert to bytes (RGBA format)
        pixel_bytes = pixels.tobytes()

        # Create ModernGL texture
        self._font_texture = self.ctx.texture((width, height), bpp, pixel_bytes)

    def _update_buffers(self, draw_data):
        """
        Update vertex and index buffers with ImGui draw data.

        Args:
            draw_data: ImGui draw data
        """
        # Collect all vertices and indices
        vertices = []
        indices = []

        global_offset = 0

        for draw_list in draw_data.cmd_lists:
            for draw_cmd in draw_list.cmd_buffer:
                # Build vertex data
                for idx in draw_cmd.elem_count:
                    vtx_idx = draw_cmd.idx_offset + idx
                    vtx = draw_list.vtx_buffer[vtx_idx]

                    # Pack vertex: pos(2f) + uv(2f) + color(4f)
                    vertices.extend(
                        [
                            vtx.pos.x,
                            vtx.pos.y,
                            vtx.uv.x,
                            vtx.uv.y,
                            vtx.col.r,
                            vtx.col.g,
                            vtx.col.b,
                            vtx.col.a,
                        ]
                    )

                # Collect indices
                for idx in draw_cmd.elem_count:
                    idx_val = draw_list.idx_buffer[draw_cmd.idx_offset + idx]
                    indices.append(global_offset + idx_val)

            # Update global offset for next draw list
            global_offset += len(draw_list.vtx_buffer)

        if not vertices:
            return

        # Convert to numpy arrays
        vertices = np.array(vertices, dtype="f4")
        indices = np.array(indices, dtype="u4")

        # Write to buffers
        self._vbo.write(vertices.tobytes())
        self._ibo.write(indices.tobytes())

    def render(self, draw_data):
        """
        Render ImGui draw data using ModernGL.

        Args:
            draw_data: ImGui draw data from imgui.render()
        """
        if draw_data is None:
            return

        # Save current OpenGL state
        self._save_state()

        # Setup OpenGL state for ImGui rendering
        self.ctx.enable(moderngl.BLEND)

        # Disable depth test for UI (UI renders on top)
        if moderngl.DEPTH_TEST in self.ctx.enabled:
            self.ctx.disable(moderngl.DEPTH_TEST)

        # Enable scissor testing
        self.ctx.enable(moderngl.SCISSOR_TEST)

        # Update buffers with new draw data
        self._update_buffers(draw_data)

        # Get IO for display settings
        io = imgui.get_io()
        display_width = io.display_size.x
        display_height = io.display_size.y

        if display_width <= 0 or display_height <= 0:
            self._restore_state()
            return

        # Calculate scale for framebuffer to window
        # Note: In pygame + moderngl, the framebuffer matches the window size
        scale_x = self.ctx.screen.width / display_width if display_width > 0 else 1
        scale_y = self.ctx.screen.height / display_height if display_height > 0 else 1

        # Create orthographic projection matrix
        # Flip Y axis (ImGui uses top-left origin, OpenGL uses bottom-left)
        projection = np.array(
            [
                [2.0 / display_width, 0.0, 0.0, 0.0],
                [0.0, 2.0 / -display_height, 0.0, 0.0],
                [0.0, 0.0, -1.0, 0.0],
                [-1.0, 1.0, 0.0, 1.0],
            ],
            dtype="f4",
        )

        # Bind texture
        self._font_texture.use(location=0)

        # Set projection uniform
        self._shader["projection"].write(projection.tobytes())

        # Track current index position
        index_offset = 0

        # Render each draw list
        for draw_list in draw_data.cmd_lists:
            for cmd in draw_list.cmd_buffer:
                # Set scissor rect (convert to OpenGL coordinates)
                # ImGui: (x, y) from top-left, y increases downward
                # OpenGL: (x, y) from bottom-left, y increases upward
                scissor_x = int(cmd.clip_rect.x * scale_x)
                scissor_y = int((display_height - cmd.clip_rect.w) * scale_y)
                scissor_w = int((cmd.clip_rect.z - cmd.clip_rect.x) * scale_x)
                scissor_h = int((cmd.clip_rect.w - cmd.clip_rect.y) * scale_y)

                self.ctx.scissor = (scissor_x, scissor_y, scissor_w, scissor_h)

                # Render the draw command
                # We need to render from index_offset to index_offset + cmd.elem_count
                self._vao.render(
                    moderngl.TRIANGLES,
                    vertices=cmd.elem_count,
                    index_array=slice(index_offset, index_offset + cmd.elem_count),
                )

                index_offset += cmd.elem_count

        # Restore OpenGL state
        self._restore_state()

    def _save_state(self):
        """Save current OpenGL state."""
        self._prev_blend_enabled = moderngl.BLEND in self.ctx.enabled
        self._prev_depth_test_enabled = moderngl.DEPTH_TEST in self.ctx.enabled
        self._prev_scissor_enabled = moderngl.SCISSOR_TEST in self.ctx.enabled

    def _restore_state(self):
        """Restore OpenGL state."""
        if self._prev_depth_test_enabled:
            self.ctx.enable(moderngl.DEPTH_TEST)
        else:
            self.ctx.disable(moderngl.DEPTH_TEST)

        if not self._prev_scissor_enabled:
            self.ctx.disable(moderngl.SCISSOR_TEST)

        # Note: We leave blend enabled as it's typically desired for 3D rendering


# Import moderngl for state checking
import moderngl
