import pkgutil
from typing import Dict, NamedTuple, Optional, Type
from game.actions.actionBase import ActionBase, ActionArgs
import importlib
import inspect

class GameAction(NamedTuple):
    action: Type[ActionBase]
    argument: Type[ActionArgs]

def actionId(action: Type[ActionBase]) -> str:
    return action.__name__

GAME_ACTIONS: Dict[str, GameAction] = {}
for pkg in pkgutil.iter_modules(__path__):
    if pkg.name in ["common", "actionBase"]:
        continue
    actionPkg = importlib.import_module(f"game.actions.{pkg.name}")

    action: Optional[Type[ActionBase]] = None
    args: Optional[Type[ActionArgs]] = None
    for name in dir(actionPkg):
        item = getattr(actionPkg, name)
        if not inspect.isclass(item):
            continue
        if issubclass(item, ActionBase):
            if action is None or issubclass(item, action):
                action = item
            elif not issubclass(action, item):
                raise RuntimeError(f"Modul {pkg.name} obsahuje dvě implementace akcí {action} a {item}")
        elif issubclass(item, ActionArgs):
            if args is None or issubclass(item, args):
                args = item
            elif not issubclass(args, item):
                raise RuntimeError(f"Modul {pkg.name} obsahuje dvě implementace argumentů {args} a {item}")
    if action is None:
        raise RuntimeError(f"Modul {pkg.name} neobsahuje implementaci akce")
    if args is None:
        raise RuntimeError(f"Modul {pkg.name} neobsahuje implementaci argumentů")
    GAME_ACTIONS[actionId(action)] = GameAction(action, args)

