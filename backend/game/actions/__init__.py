import importlib
import inspect
import pkgutil
from typing import NamedTuple, Optional, Type

from game.actions.actionBase import (
    ActionArgs,
    ActionCommonBase,
    NoInitActionBase,
    TeamActionArgs,
    TeamActionBase,
    TeamInteractionActionBase,
)


class GameAction(NamedTuple):
    action: Type[ActionCommonBase]
    argument: Type[ActionArgs]


def actionId(action: Type[ActionCommonBase]) -> str:
    return action.__name__


def checkGameAction(action: Type[ActionCommonBase], args: Type[ActionArgs]) -> None:
    assert issubclass(action, ActionCommonBase)
    assert issubclass(args, ActionArgs)

    if issubclass(action, TeamActionBase):
        assert issubclass(args, TeamActionArgs)
    assert not (
        issubclass(action, TeamInteractionActionBase)
        and issubclass(action, NoInitActionBase)
    )


def loadActions() -> dict[str, GameAction]:
    gameActions: dict[str, GameAction] = {}
    for pkg in pkgutil.iter_modules(__path__):
        if pkg.name in ["common", "actionBase"]:
            continue
        actionPkg = importlib.import_module(f"game.actions.{pkg.name}")

        actions: list[Type[ActionCommonBase]] = []
        args: Optional[Type[ActionArgs]] = None
        for name in dir(actionPkg):
            item = getattr(actionPkg, name)
            if not inspect.isclass(item):
                continue
            if item in (
                ActionCommonBase,
                NoInitActionBase,
                TeamActionBase,
                TeamInteractionActionBase,
                TeamActionArgs,
            ):
                continue
            if issubclass(item, ActionCommonBase):
                actions.append(item)
            elif issubclass(item, ActionArgs):
                if args is None or issubclass(item, args):
                    args = item
                elif not issubclass(args, item):
                    raise RuntimeError(
                        f"Modul {pkg.name} obsahuje dvě implementace argumentů {args} a {item}"
                    )
        if len(actions) == 0:
            raise RuntimeError(f"Modul {pkg.name} neobsahuje implementaci akce")
        if args is None:
            raise RuntimeError(f"Modul {pkg.name} neobsahuje implementaci argumentů")
        for action in actions:
            checkGameAction(action, args)
            assert (
                actionId(action) not in gameActions
            ), f"Multiple Actions with same name {actionId(action)}"
            gameActions[actionId(action)] = GameAction(action, args)
    return gameActions


GAME_ACTIONS: dict[str, GameAction] = loadActions()
