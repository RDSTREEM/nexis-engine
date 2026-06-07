"""
undo_redo.py
Command-pattern undo/redo stack.
All editor operations that modify scene state go through here.

Usage:
    from core.undo_redo import UndoStack
    UndoStack.execute(MoveEntityCommand(entity, old_pos, new_pos))
    UndoStack.undo()   # Ctrl+Z
    UndoStack.redo()   # Ctrl+Y
"""
from __future__ import annotations
import copy
from typing import List, Optional
import numpy as np


# ------------------------------------------------------------------
# Base command
# ------------------------------------------------------------------

class Command:
    description: str = "Command"

    def execute(self) -> None: ...
    def undo(self)    -> None: ...


# ------------------------------------------------------------------
# Concrete commands
# ------------------------------------------------------------------

class MoveEntityCommand(Command):
    def __init__(self, entity, old_pos: np.ndarray, new_pos: np.ndarray):
        self.entity  = entity
        self.old_pos = old_pos.copy()
        self.new_pos = new_pos.copy()
        self.description = f"Move '{entity.name}'"

    def execute(self) -> None:
        self.entity.transform.position[:] = self.new_pos
        self.entity.transform._dirty      = True

    def undo(self) -> None:
        self.entity.transform.position[:] = self.old_pos
        self.entity.transform._dirty      = True


class RotateEntityCommand(Command):
    def __init__(self, entity, old_rot: np.ndarray, new_rot: np.ndarray):
        self.entity  = entity
        self.old_rot = old_rot.copy()
        self.new_rot = new_rot.copy()
        self.description = f"Rotate '{entity.name}'"

    def execute(self) -> None:
        self.entity.transform.rotation[:] = self.new_rot
        self.entity.transform._dirty      = True

    def undo(self) -> None:
        self.entity.transform.rotation[:] = self.old_rot
        self.entity.transform._dirty      = True


class ScaleEntityCommand(Command):
    def __init__(self, entity, old_scl: np.ndarray, new_scl: np.ndarray):
        self.entity  = entity
        self.old_scl = old_scl.copy()
        self.new_scl = new_scl.copy()
        self.description = f"Scale '{entity.name}'"

    def execute(self) -> None:
        self.entity.transform.scale[:] = self.new_scl
        self.entity.transform._dirty   = True

    def undo(self) -> None:
        self.entity.transform.scale[:] = self.old_scl
        self.entity.transform._dirty   = True


class AddEntityCommand(Command):
    def __init__(self, scene, entity):
        self.scene  = scene
        self.entity = entity
        self.description = f"Add '{entity.name}'"

    def execute(self) -> None:
        self.scene.add_entity(self.entity)

    def undo(self) -> None:
        self.scene.remove_entity(self.entity)


class DeleteEntityCommand(Command):
    def __init__(self, scene, entity):
        self.scene       = scene
        self.entity      = entity
        self.parent      = entity._parent
        self.description = f"Delete '{entity.name}'"

    def execute(self) -> None:
        self.scene.remove_entity(self.entity)

    def undo(self) -> None:
        if self.parent:
            self.parent.add_child(self.entity)
        else:
            self.scene.add_entity(self.entity)


class RenameEntityCommand(Command):
    def __init__(self, entity, old_name: str, new_name: str):
        self.entity   = entity
        self.old_name = old_name
        self.new_name = new_name
        self.description = f"Rename '{old_name}' → '{new_name}'"

    def execute(self) -> None:
        self.entity.name = self.new_name

    def undo(self) -> None:
        self.entity.name = self.old_name


class ReparentEntityCommand(Command):
    def __init__(self, entity, old_parent, new_parent, scene):
        self.entity     = entity
        self.old_parent = old_parent
        self.new_parent = new_parent
        self.scene      = scene
        self.description = f"Reparent '{entity.name}'"

    def execute(self) -> None:
        if self.new_parent:
            self.new_parent.add_child(self.entity)
        else:
            self.entity.detach_from_parent()

    def undo(self) -> None:
        if self.old_parent:
            self.old_parent.add_child(self.entity)
        else:
            self.entity.detach_from_parent()


class SetPropertyCommand(Command):
    """Generic: set any attribute on any object."""
    def __init__(self, obj, attr: str, old_val, new_val, label=""):
        self.obj     = obj
        self.attr    = attr
        self.old_val = copy.deepcopy(old_val)
        self.new_val = copy.deepcopy(new_val)
        self.description = label or f"Set {attr}"

    def execute(self) -> None:
        cur = getattr(self.obj, self.attr)
        if hasattr(cur, "__setitem__") and hasattr(self.new_val, "__iter__"):
            for i, v in enumerate(self.new_val): cur[i] = v
        else:
            setattr(self.obj, self.attr, self.new_val)

    def undo(self) -> None:
        cur = getattr(self.obj, self.attr)
        if hasattr(cur, "__setitem__") and hasattr(self.old_val, "__iter__"):
            for i, v in enumerate(self.old_val): cur[i] = v
        else:
            setattr(self.obj, self.attr, self.old_val)


class CompoundCommand(Command):
    """Groups multiple commands into one undo step."""
    def __init__(self, commands: list, description="Compound"):
        self.commands    = commands
        self.description = description

    def execute(self) -> None:
        for c in self.commands: c.execute()

    def undo(self) -> None:
        for c in reversed(self.commands): c.undo()


# ------------------------------------------------------------------
# Stack singleton
# ------------------------------------------------------------------

class _UndoStack:
    MAX = 100

    def __init__(self):
        self._undo: List[Command] = []
        self._redo: List[Command] = []
        self._on_change = None   # callback for UI update

    def set_on_change(self, fn) -> None:
        self._on_change = fn

    def execute(self, cmd: Command) -> None:
        cmd.execute()
        self._undo.append(cmd)
        if len(self._undo) > self.MAX:
            self._undo.pop(0)
        self._redo.clear()
        self._notify()

    def undo(self) -> Optional[str]:
        if not self._undo:
            return None
        cmd = self._undo.pop()
        cmd.undo()
        self._redo.append(cmd)
        self._notify()
        return cmd.description

    def redo(self) -> Optional[str]:
        if not self._redo:
            return None
        cmd = self._redo.pop()
        cmd.execute()
        self._undo.append(cmd)
        self._notify()
        return cmd.description

    def clear(self) -> None:
        self._undo.clear()
        self._redo.clear()
        self._notify()

    def can_undo(self) -> bool: return bool(self._undo)
    def can_redo(self) -> bool: return bool(self._redo)

    def undo_description(self) -> str:
        return self._undo[-1].description if self._undo else ""

    def redo_description(self) -> str:
        return self._redo[-1].description if self._redo else ""

    def _notify(self) -> None:
        if self._on_change:
            self._on_change()


UndoStack = _UndoStack()