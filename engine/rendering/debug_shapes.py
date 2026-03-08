def draw_grid(debug_renderer, size=10, step=1):
    for i in range(-size, size + 1, step):
        debug_renderer.draw_line(
            (i, 0, -size),
            (i, 0, size),
        )
        debug_renderer.draw_line(
            (-size, 0, i),
            (size, 0, i),
        )


def draw_axis(debug_renderer):
    debug_renderer.draw_line((0, 0, 0), (5, 0, 0))
    debug_renderer.draw_line((0, 0, 0), (0, 5, 0))
    debug_renderer.draw_line((0, 0, 0), (0, 0, 5))


def draw_grid_2d(debug_renderer, size=10, step=1):
    for i in range(-size, size + 1, step):
        debug_renderer.draw_line(
            (i, -size, 0),
            (i, size, 0),
        )
        debug_renderer.draw_line(
            (-size, i, 0),
            (size, i, 0),
        )
