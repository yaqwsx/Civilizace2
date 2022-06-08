import json
import traceback
from typing import Any, Dict, List, Set, Tuple
from game.actions.common import ActionFailed, MessageBuilder

from game.entities import DieId
from game.gameGlue import stateSerialize
from game.state import GameState
from .actionBase import ActionBase, ActionArgs, ActionResult

class GodModeArgs(ActionArgs):
    change: Dict[str, str]
    add: Dict[str, str]
    remove: Dict[str, str]
    original: GameState

class GodModeAction(ActionBase):
    @property
    def args(self) -> GodModeArgs:
        assert isinstance(self._generalArgs, GodModeArgs)
        return self._generalArgs

    def diceRequirements(self) -> Tuple[Set[DieId], int]:
        return (set(), 0)

    def applyInitiate(self) -> ActionResult:
        self.description = "God mode. Smiř se s tím."
        return ActionResult(expected=True, message="")

    def applyCommit(self, throws: int, dots: int) -> ActionResult:
        self._setupPrivateAttrs()
        self._ensureNoChange()

        for path, v in self.args.change.items():
            p = path.split(".")
            self._changeRec(p, self.state, json.loads(v), path)
        for path, vals in self.args.add.items():
            for v in json.loads(vals):
                p = path.split(".")
                self._addRec(p, self.state, v, path)
        for path, vals in self.args.remove.items():
            for v in json.loads(vals):
                p = path.split(".")
                self._deleteRec(p, self.state, v, path)

        if not self._errors.empty:
            raise ActionFailed(self._errors)
        try:
            stateSerialize(self.state)
        except Exception as e:
            tb = traceback.format_exc()
            raise ActionFailed(f"Upravený stav není možné serializovat:\n\n```\n{tb}\n```")

        return ActionResult(expected=True, message="Úspěšně provedeno")

    def _ensureNoChange(self):
        """
        Ensures that the relevant pieces of the state weren't changed in between
        """
        pass # TBA

    def _changeRec(self, path: List[str], object, value, originalPath):
        key = self.entities.get(path[0], path[0])
        if len(path) == 1:
            value = self.entities.get(value, value)
            if isinstance(object, dict):
                object[key] = value
                return
            if not hasattr(object, key):
                self._errors.add(f"Neznámý klíč {originalPath}")
                return
            setattr(object, key, value)
            return
        if isinstance(object, dict):
            newObj = object[key]
        else:
            newObj = getattr(object, key)
        self._changeRec(path[1:], newObj, value, originalPath)

    def _addRec(self, path: List[str], object, value, originalPath):
        if len(path) == 0:
            value = self.entities.get(value, value)
            if isinstance(object, list):
                object.append(value)
            elif isinstance(object, set):
                object.add(value)
            else:
                raise RuntimeError("Unknown object")
            return
        key = self.entities.get(path[0], path[0])
        if isinstance(object, dict):
            newObj = object[key]
        else:
            newObj = getattr(object, key)
        self._addRec(path[1:], newObj, value, originalPath)

    def _deleteRec(self, path: List[str], object, value, originalPath):
        if len(path) == 0:
            value = self.entities.get(value, value)
            if isinstance(object, list) or isinstance(object, set):
                object.remove(value)
            else:
                raise RuntimeError("Unknown object")
            return
        key = self.entities.get(path[0], path[0])
        if isinstance(object, dict):
            newObj = object[key]
        else:
            newObj = getattr(object, key)
        self._deleteRec(path[1:], newObj, value, originalPath)





