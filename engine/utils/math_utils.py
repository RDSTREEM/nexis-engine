import numpy as np


def create_translation(position):
    mat = np.identity(4, dtype="f4")
    mat[0:3, 3] = position[0:3]
    return mat


def create_scale(scale):
    mat = np.identity(4, dtype="f4")
    mat[0][0] = scale[0]
    mat[1][1] = scale[1]
    mat[2][2] = scale[2]
    return mat


def create_perspective(fov, aspect, near, far):
    f = 1.0 / np.tan(np.radians(fov) / 2)
    mat = np.zeros((4, 4), dtype="f4")

    mat[0][0] = f / aspect
    mat[1][1] = f
    mat[2][2] = (far + near) / (near - far)
    mat[2][3] = (2 * far * near) / (near - far)
    mat[3][2] = -1

    return mat


def create_orthographic(left, right, bottom, top, near, far):
    mat = np.identity(4, dtype="f4")

    mat[0][0] = 2.0 / (right - left)
    mat[1][1] = 2.0 / (top - bottom)
    mat[2][2] = -2.0 / (far - near)

    mat[0][3] = -(right + left) / (right - left)
    mat[1][3] = -(top + bottom) / (top - bottom)
    mat[2][3] = -(far + near) / (far - near)

    return mat


def create_rotation_x(angle):
    rad = np.radians(angle)
    c = np.cos(rad)
    s = np.sin(rad)

    mat = np.identity(4, dtype="f4")
    mat[1][1] = c
    mat[1][2] = -s
    mat[2][1] = s
    mat[2][2] = c
    return mat


def create_rotation_y(angle):
    rad = np.radians(angle)
    c = np.cos(rad)
    s = np.sin(rad)

    mat = np.identity(4, dtype="f4")
    mat[0][0] = c
    mat[0][2] = s
    mat[2][0] = -s
    mat[2][2] = c
    return mat


def create_rotation_z(angle):
    rad = np.radians(angle)
    c = np.cos(rad)
    s = np.sin(rad)

    mat = np.identity(4, dtype="f4")
    mat[0][0] = c
    mat[0][1] = -s
    mat[1][0] = s
    mat[1][1] = c
    return mat


def forward_vector(rotation):
    pitch = np.radians(rotation[0])
    yaw = np.radians(rotation[1])

    return np.array(
        [
            -np.sin(yaw) * np.cos(pitch),
            -np.sin(pitch),
            -np.cos(yaw) * np.cos(pitch),
        ],
        dtype="f4",
    )


def screen_point_to_ray(mouse_pos, camera, screen_width, screen_height):
    x, y = mouse_pos
    ndc_x = (2.0 * x) / screen_width - 1.0
    ndc_y = 1.0 - (2.0 * y) / screen_height

    projection = camera.get_projection_matrix(screen_width / screen_height)
    view = camera.get_view_matrix()

    inv_proj = np.linalg.inv(projection)
    inv_view = np.linalg.inv(view)

    near_point = np.array([ndc_x, ndc_y, -1.0, 1.0], dtype="f4")
    far_point = np.array([ndc_x, ndc_y, 1.0, 1.0], dtype="f4")

    world_near = inv_view @ (inv_proj @ near_point)
    world_far = inv_view @ (inv_proj @ far_point)

    if world_near[3] != 0:
        world_near /= world_near[3]
    if world_far[3] != 0:
        world_far /= world_far[3]

    origin = world_near[0:3]
    direction = world_far[0:3] - origin
    norm = np.linalg.norm(direction)
    if norm != 0:
        direction = direction / norm

    return origin, direction


def get_ground_intersection(
    mouse_pos, camera, screen_width, screen_height, plane_y=0.0
):
    origin, direction = screen_point_to_ray(
        mouse_pos, camera, screen_width, screen_height
    )

    if abs(direction[1]) < 1e-6:
        return None

    t = (plane_y - origin[1]) / direction[1]
    if t < 0:
        return None

    return origin + direction * t
