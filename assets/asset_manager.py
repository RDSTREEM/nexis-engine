"""
asset_manager.py
Central registry for all imported assets.
Assets are keyed by their absolute path string.
Importers register themselves for file extensions.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Callable, Dict, Optional, List
from dataclasses import dataclass, field


@dataclass
class Asset:
    path: str
    name: str
    asset_type: str  # "mesh", "texture", "audio", "script"
    data: Any = None  # runtime object (np.ndarray, moderngl.Texture, etc.)
    meta: Dict = field(default_factory=dict)

    @property
    def uid(self) -> str:
        return hashlib.md5(self.path.encode()).hexdigest()[:12]

    def is_loaded(self) -> bool:
        return self.data is not None


EXTENSION_MAP: Dict[str, str] = {
    # mesh
    ".obj": "mesh",
    ".fbx": "mesh",
    ".gltf": "mesh",
    ".glb": "mesh",
    # texture
    ".png": "texture",
    ".jpg": "texture",
    ".jpeg": "texture",
    ".bmp": "texture",
    ".tga": "texture",
    ".hdr": "texture",
    # audio
    ".wav": "audio",
    ".mp3": "audio",
    ".ogg": "audio",
    ".flac": "audio",
    # script
    ".py": "script",
    ".amh": "script",
}


class AssetManager:
    def __init__(self, app):
        self.app = app
        self._assets: Dict[str, Asset] = {}
        self._importers: Dict[str, Callable] = {}

    # ------------------------------------------------------------------
    # Importer registration
    # ------------------------------------------------------------------

    def register_importer(self, asset_type: str, fn: Callable) -> None:
        self._importers[asset_type] = fn

    # ------------------------------------------------------------------
    # Import
    # ------------------------------------------------------------------

    def import_file(self, path: str | Path, force: bool = False) -> Optional[Asset]:
        path = Path(path).resolve()
        key = str(path)

        if key in self._assets and not force:
            return self._assets[key]

        ext = path.suffix.lower()
        atype = EXTENSION_MAP.get(ext)
        if atype is None:
            self.app.console.warning(f"AssetManager: unsupported extension '{ext}'")
            return None

        importer = self._importers.get(atype)
        if importer is None:
            self.app.console.warning(
                f"AssetManager: no importer registered for type '{atype}'"
            )
            return None

        try:
            data = importer(path)
            asset = Asset(
                path=key,
                name=path.stem,
                asset_type=atype,
                data=data,
            )
            self._assets[key] = asset
            self.app.console.info(f"Imported {atype}: {path.name}")
            return asset
        except Exception as exc:
            self.app.console.warning(
                f"AssetManager: import failed for {path.name}: {exc}"
            )
            return None

    # ------------------------------------------------------------------
    # Scan project folder
    # ------------------------------------------------------------------

    def scan_project(self, root: Path) -> List[Asset]:
        assets_dir = root / "assets"
        if not assets_dir.exists():
            return []
        imported = []
        for f in assets_dir.rglob("*"):
            if f.is_file() and f.suffix.lower() in EXTENSION_MAP:
                a = self.import_file(f)
                if a:
                    imported.append(a)
        return imported

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get(self, path: str) -> Optional[Asset]:
        return self._assets.get(str(Path(path).resolve()))

    def get_by_type(self, asset_type: str) -> List[Asset]:
        return [a for a in self._assets.values() if a.asset_type == asset_type]

    def all_assets(self) -> List[Asset]:
        return list(self._assets.values())

    def unload(self, path: str) -> None:
        key = str(Path(path).resolve())
        if key in self._assets:
            del self._assets[key]
