"""
entity_templates.py
Factory functions for common entity types.
FIX: Removed stale Material/Shader imports. mesh_entity no longer passes
     Material directly — MeshRenderer handles its own default material.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.entity import Entity
    from core.scene import Scene


def _make(scene: "Scene", name: str) -> "Entity":
    from core.entity import Entity

    return Entity(name=name, scene=scene)


# ── General ──────────────────────────────────────────────────────────────────


def empty_entity(scene, name="Empty") -> "Entity":
    return _make(scene, name)


def group_entity(scene, name="Group") -> "Entity":
    e = _make(scene, name)
    e.tags.append("group")
    return e


# ── 3D ───────────────────────────────────────────────────────────────────────


def mesh_entity(scene, name="Mesh", primitive="cube") -> "Entity":
    from core.mesh_renderer import MeshRenderer

    e = _make(scene, name)
    # MeshRenderer creates its own Material with the correct shader internally
    mr = MeshRenderer(primitive=primitive)
    e.add_component(mr)
    return e


def camera_entity_3d(scene, name="Camera") -> "Entity":
    from core.camera_component import CameraComponent

    e = _make(scene, name)
    cc = CameraComponent(projection="perspective", fov=45.0)
    e.add_component(cc)
    e.transform.set_position(0, 2, 8)
    return e


def directional_light_entity(scene, name="Directional Light") -> "Entity":
    e = _make(scene, name)
    e.tags.append("light")
    e.transform.set_rotation(-45, 0, 0)
    return e


# ── 2D ───────────────────────────────────────────────────────────────────────


def sprite_entity(scene, name="Sprite") -> "Entity":
    from core.sprite_renderer import SpriteRenderer

    e = _make(scene, name)
    sr = SpriteRenderer(shape="square")
    e.add_component(sr)
    return e


def shape_entity(scene, name="Shape", shape="square") -> "Entity":
    from core.sprite_renderer import Shape2DRenderer

    e = _make(scene, name)
    e.add_component(Shape2DRenderer(shape=shape))
    return e


def camera_entity_2d(scene, name="Camera 2D") -> "Entity":
    from core.camera_component import CameraComponent

    e = _make(scene, name)
    cc = CameraComponent(projection="orthographic", ortho_size=5.0)
    e.add_component(cc)
    return e


def tilemap_entity(scene, name="Tilemap") -> "Entity":
    e = _make(scene, name)
    e.tags.append("tilemap")
    return e


# ── Physics ───────────────────────────────────────────────────────────────────


def rigidbody_entity(scene, name="Rigidbody", shape="square") -> "Entity":
    from core.sprite_renderer import Shape2DRenderer
    from core.physics_2d import Rigidbody2D, BoxCollider2D

    e = _make(scene, name)
    e.add_component(Shape2DRenderer(shape=shape))
    e.add_component(BoxCollider2D(width=1.0, height=1.0))
    e.add_component(Rigidbody2D())
    return e


def static_body_entity(scene, name="Static Body", shape="square") -> "Entity":
    from core.sprite_renderer import Shape2DRenderer
    from core.physics_2d import BoxCollider2D, Rigidbody2D

    e = _make(scene, name)
    e.add_component(Shape2DRenderer(shape=shape))
    e.add_component(BoxCollider2D(width=1.0, height=1.0))
    rb = Rigidbody2D()
    rb.is_kinematic = True
    rb.gravity_scale = 0
    e.add_component(rb)
    return e


def trigger_entity(scene, name="Trigger") -> "Entity":
    from core.physics_2d import BoxCollider2D

    e = _make(scene, name)
    c = BoxCollider2D(width=1.0, height=1.0)
    c.is_trigger = True
    e.add_component(c)
    return e


# ── Audio ─────────────────────────────────────────────────────────────────────


def audio_entity(scene, name="Audio Source") -> "Entity":
    from core.audio_source import AudioSource

    e = _make(scene, name)
    e.tags.append("audio")
    e.add_component(AudioSource())
    return e


# ── Scripted ──────────────────────────────────────────────────────────────────


def scripted_entity(scene, name="Scripted Entity") -> "Entity":
    from core.script_component import ScriptComponent

    e = _make(scene, name)
    e.add_component(ScriptComponent())
    return e


# ── Registry ──────────────────────────────────────────────────────────────────

TEMPLATES = {
    "Empty": (empty_entity, "General", "Bare entity with only a Transform"),
    "Group": (group_entity, "General", "Empty container for organising entities"),
    "Mesh (Cube)": (
        lambda s: mesh_entity(s, "Mesh", "cube"),
        "3D",
        "Cube mesh with default material",
    ),
    "Mesh (Sphere)": (lambda s: mesh_entity(s, "Mesh", "sphere"), "3D", "Sphere mesh"),
    "Mesh (Plane)": (lambda s: mesh_entity(s, "Mesh", "plane"), "3D", "Plane mesh"),
    "Mesh (Cylinder)": (
        lambda s: mesh_entity(s, "Mesh", "cylinder"),
        "3D",
        "Cylinder mesh",
    ),
    "Mesh (Cone)": (lambda s: mesh_entity(s, "Mesh", "cone"), "3D", "Cone mesh"),
    "Mesh (Capsule)": (
        lambda s: mesh_entity(s, "Mesh", "capsule"),
        "3D",
        "Capsule mesh",
    ),
    "Mesh (Torus)": (lambda s: mesh_entity(s, "Mesh", "torus"), "3D", "Torus mesh"),
    "Camera 3D": (camera_entity_3d, "3D", "Perspective camera entity"),
    "Sprite": (sprite_entity, "2D", "Sprite with SpriteRenderer"),
    "Shape": (shape_entity, "2D", "Solid colour 2D shape"),
    "Camera 2D": (camera_entity_2d, "2D", "Orthographic camera entity"),
    "Rigidbody": (rigidbody_entity, "Physics", "2D physics body with collider"),
    "Static Body": (static_body_entity, "Physics", "Immovable collider"),
    "Trigger": (trigger_entity, "Physics", "Trigger collider"),
    "Audio Source": (audio_entity, "Audio", "Audio source entity"),
    "Scripted Entity": (scripted_entity, "Script", "Entity with a ScriptComponent"),
}
