"""
prefab_system.py
Save any entity (+ children) as a .nexis_prefab file.
Instantiate prefabs into a scene — supports overrides.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from core.entity import Entity
    from core.scene  import Scene


PREFAB_EXT = ".nexis_prefab"


class PrefabSystem:
    def __init__(self, app):
        self.app = app

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def save_prefab(self, entity: "Entity",
                    path: Optional[Path] = None) -> Path:
        """
        Serialise entity + all children to a .nexis_prefab JSON file.
        If path is None, saves to project/assets/prefabs/<name>.nexis_prefab
        """
        if path is None:
            prefabs_dir = (self.app.project.project_root or Path(".")) \
                          / "assets" / "prefabs"
            prefabs_dir.mkdir(parents=True, exist_ok=True)
            path = prefabs_dir / f"{entity.name}{PREFAB_EXT}"

        data = {
            "prefab_version": "1",
            "root":           entity.to_dict(),
        }
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self.app.console.info(f"Saved prefab: {path.name}")
        return path

    # ------------------------------------------------------------------
    # Load / instantiate
    # ------------------------------------------------------------------

    def instantiate(self, path: Path | str,
                    scene: "Scene",
                    overrides: Optional[Dict[str, Any]] = None) -> "Entity":
        """
        Load a prefab and add it to scene.
        overrides: dict of {dot.path: value} applied after instantiation
        e.g. {"transform.position": [1, 2, 0], "name": "Enemy_1"}
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Prefab not found: {path}")

        data  = json.loads(path.read_text(encoding="utf-8"))
        root  = data.get("root", data)   # backwards compat

        from core.entity import Entity
        import uuid
        # give it a fresh id so it's a new instance
        root["id"]   = str(uuid.uuid4())

        entity = Entity.from_dict(root, scene=scene)
        self._regen_ids(entity)   # fresh ids for all children too

        # apply overrides
        if overrides:
            self._apply_overrides(entity, overrides)

        scene.add_entity(entity)
        self.app.console.info(
            f"Instantiated prefab '{path.stem}' as '{entity.name}'")
        return entity

    def _regen_ids(self, entity: "Entity") -> None:
        import uuid
        entity.id = str(uuid.uuid4())
        for child in entity.children:
            self._regen_ids(child)

    def _apply_overrides(self, entity: "Entity",
                         overrides: Dict[str, Any]) -> None:
        for key, value in overrides.items():
            parts = key.split(".")
            obj   = entity
            for part in parts[:-1]:
                obj = getattr(obj, part, None)
                if obj is None:
                    break
            if obj is not None:
                attr = parts[-1]
                current = getattr(obj, attr, None)
                if current is not None and hasattr(current, "__setitem__"):
                    # numpy array or list
                    for i, v in enumerate(value):
                        current[i] = v
                else:
                    setattr(obj, attr, value)

    # ------------------------------------------------------------------
    # List prefabs in project
    # ------------------------------------------------------------------

    def list_prefabs(self) -> list[Path]:
        if self.app.project.project_root is None:
            return []
        prefab_dir = self.app.project.project_root / "assets" / "prefabs"
        if not prefab_dir.exists():
            return []
        return list(prefab_dir.glob(f"*{PREFAB_EXT}"))