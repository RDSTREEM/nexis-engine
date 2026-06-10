"""
camera_auto.py
Auto-creates a main camera in new scenes so Play mode is never a black screen.
"""

from __future__ import annotations


def ensure_camera(scene, scene_type: str = "3D") -> None:
    from core.camera_component import CameraComponent
    from core.entity import Entity

    for entity in scene.all_entities():
        cam = entity.get_component(CameraComponent)
        if cam and cam.is_main:
            return

    cam_entity = Entity(name="Main Camera", scene=scene)
    cam_comp = CameraComponent()
    cam_comp.is_main = True

    if scene_type == "2D":
        cam_comp.projection = "orthographic"
        cam_comp.ortho_size = 6.0
        cam_entity.transform.position[:] = [0, 0, 10]
    else:
        cam_comp.projection = "perspective"
        cam_comp.fov = 60.0
        cam_entity.transform.position[:] = [0, 3, 8]
        cam_entity.transform.rotation[:] = [-15, 0, 0]

    cam_entity.add_component(cam_comp)
    scene.add_entity(cam_entity)
