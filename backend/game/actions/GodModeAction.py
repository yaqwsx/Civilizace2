import json
import traceback
from typing import Any, Dict, List, Set, Tuple
from game.actions.common import ActionFailed, MessageBuilder

from game.entities import DieId
from game.gameGlue import stateDeserialize, stateSerialize
from game.state import GameState
from .actionBase import ActionBase, ActionArgs, ActionResult

class GodModeArgs(ActionArgs):
    change: Dict[str, str]
    add: Dict[str, str]
    remove: Dict[str, str]
    original: GameState

class GodModeAction(ActionBase):
    @property
    def description(self):
        return "Godmode"

    @property
    def args(self) -> GodModeArgs:
        assert isinstance(self._generalArgs, GodModeArgs)
        return self._generalArgs

    def diceRequirements(self) -> Tuple[Set[DieId], int]:
        return (set(), 0)

    def applyInitiate(self) -> ActionResult:
        return ActionResult(expected=True, message="")

    def applyCommit(self, throws: int, dots: int) -> ActionResult:
        self._setupPrivateAttrs()
        self._ensureNoChange()

        for path, v in self.args.change.items():
            p = path.split(".")
            self._changeRec(p, self.state, json.loads(v), path)
        for path, vals in self.args.add.items():
            for v in json.loads(vals):
                if isinstance(v, str) and len(v) == 0:
                    self._errors.add(f"Nemůžu přidat prázdný řetězec do klíče {path}")
                else:
                    p = path.split(".")
                    self._addRec(p, self.state, v, path)
        for path, vals in self.args.remove.items():
            for v in json.loads(vals):
                p = path.split(".")
                self._deleteRec(p, self.state, v, path)

        if not self._errors.empty:
            raise ActionFailed(self._errors)
        try:
            x = stateSerialize(self.state)
            stateDeserialize(GameState, x, self.entities)
        except Exception as e:
            tb = traceback.format_exc()
            raise ActionFailed(f"Upravený stav není možné serializovat:\n\n```\n{tb}\n```")

        return ActionResult(expected=True, message="Úspěšně provedeno")

    def _ensureNoChange(self):
        """
        Ensures that the relevant pieces of the state weren't changed in between
        """
        paths = set()
        paths.update(self.args.change.keys())
        paths.update(self.args.add.keys())
        paths.update(self.args.remove.keys())
        for p in paths:
            p = p.split(".")
            if p[0] == "teamStates":
                t = self.entities[p[1]]
                if self.state.teamStates[t] != self.args.original.teamStates[t]:
                    self._errors.add(f"Chcete měnit stav týmu {t.name}, ale v průběhu editace se jejich stav změnil. Zadejte znovu.")
            if p[0] == "world":
                if self.state.world != self.args.original.world:
                    self._errors.add(f"Stav světa se změnil během vašich úprav, prosím opakujte")
            if p[0] == "map":
                if self.state.map != self.args.original.map:
                    self._errors.add(f"Stav mapy se změnil během vašich úprav, prosím opakujte")
        if not self._errors.empty:
            raise ActionFailed(self._errors)

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
        key = self.entities.get(path[0], path[0])
        if len(path) == 1 and isinstance(object, dict):
            if key not in object or not isinstance(object[key], list):
                object[key] = value
                return
        if len(path) == 0:
            value = self.entities.get(value, value)
            if isinstance(object, list):
                object.append(value)
            elif isinstance(object, set):
                object.add(value)
            else:
                raise RuntimeError("Unknown object")
            return
        if isinstance(object, dict):
            newObj = object[key]
        else:
            newObj = getattr(object, key)
        self._addRec(path[1:], newObj, value, originalPath)

    def _deleteRec(self, path: List[str], object, value, originalPath):
        if len(path) == 1 and isinstance(object, dict):
            if key in object and not isinstance(object[key], list):
                del object[key]
                return
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




