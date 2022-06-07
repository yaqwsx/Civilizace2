import pkgutil
from game.actions.actionBase import ActionInterface, ActionArgs
from collections import namedtuple
import importlib
import inspect

GameAction = namedtuple("GameAction", ["action", "argument"])

def actionId(action):
    return action.__name__

GAME_ACTIONS = {}
for pkg in pkgutil.iter_modules(__path__):
    if pkg.name in ["common", "actionBase"]:
        continue
    actionPkg = importlib.import_module(f"game.actions.{pkg.name}")

    action = None
    args = None
    for name in dir(actionPkg):
        item = getattr(actionPkg, name)
        if not inspect.isclass(item):
            continue
        if issubclass(item, ActionInterface):
            if action is None or not issubclass(action, item):
                action = item
        elif issubclass(item, ActionArgs):
            if args is None or not issubclass(args, item):
                args = item
    if action is None:
        raise RuntimeError(f"Modul {pkg.name} neobsahuje implementaci akce")
    if args is None:
        raise RuntimeError(f"Modul {pkg.name} neobsahuje implementaci argumentů")
    GAME_ACTIONS[actionId(action)] = GameAction(action, args)

