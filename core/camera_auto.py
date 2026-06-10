"""
camera_auto.py
Utility: ensure new scenes always have a main camera entity.
Call `ensure_camera(scene, scene_type)` after creating or loading a scene.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.scene import Scene


def ensure_camera(scene: "Scene", scene_type: str = "3D") -> None:
    """
    If the scene has no entity with a CameraComponent marked is_main,
    create one at a sensible default position.
    """
    from core.camera_component import CameraComponent
    from core.entity import Entity

    for entity in scene.all_entities():
        cam = entity.get_component(CameraComponent)
        if cam and cam.is_main:
            return   # already has one

    # Create camera
    cam_entity = Entity(name="Main Camera", scene=scene)
    cam_comp   = CameraComponent()
    cam_comp.is_main   = True

    if scene_type == "2D":
        cam_comp.projection = "orthographic"
        cam_entity.transform.position[:] = [0, 0, 10]
    else:
        cam_comp.projection = "perspective"
        cam_comp.fov        = 60.0
        cam_entity.transform.position[:] = [0, 3, 8]
        cam_entity.transform.rotation[:] = [-15, 0, 0]

    cam_entity.add_component(cam_comp)
    scene.add_entity(cam_entity)
