from enum import Enum
from typing import Any, Dict, Type
import typing
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from game.actions import GAME_ACTIONS, GameAction, actionId
from game.actions.actionBase import (
    ActionCommonBase,
    NoInitActionBase,
    TeamInteractionActionBase,
)
from game.viewsets.permissions import IsOrg
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.request import Request
from pydantic.fields import ModelField


class ActionViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated, IsOrg)

    @staticmethod
    def typeInfo(outer_type: Type) -> Dict[str, Any]:
        if isinstance(outer_type, type):
            if issubclass(outer_type, Enum):
                return {
                    "type": "Enum",
                    "values": {
                        name: value.value
                        for name, value in outer_type._member_map_.items()
                    },
                }
            return {"type": outer_type.__name__}
        if typing.get_origin(outer_type) is not None:
            return {
                "type": typing.get_origin(outer_type).__name__,
                "subtypes": [
                    ActionViewSet.typeInfo(subtype)
                    for subtype in typing.get_args(outer_type)
                ],
            }
        assert False, f"Not expected type {outer_type} (check if it's a ForwardRef)"

    @staticmethod
    def fieldInfo(field: ModelField) -> Dict[str, Any]:
        info = ActionViewSet.typeInfo(field.outer_type_)
        info["required"] = bool(field.required)
        if not field.required:
            info["default"] = field.get_default()
        return info

    @staticmethod
    def serialize_action(action: GameAction):
        assert isinstance(action.action, type)
        assert issubclass(action.action, ActionCommonBase)
        assert issubclass(action.action, TeamInteractionActionBase | NoInitActionBase)

        args = {
            name: ActionViewSet.fieldInfo(field)
            for name, field in action.argument.__fields__.items()
        }

        return {
            "id": actionId(action.action),
            "has_init": issubclass(action.action, TeamInteractionActionBase),
            "args": args,
        }

    def list(self, request: Request):
        return Response(
            [ActionViewSet.serialize_action(action) for action in GAME_ACTIONS.values()]
        )
