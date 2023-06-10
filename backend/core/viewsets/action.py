import typing
from enum import Enum
from typing import Any, Type

from pydantic.fields import ModelField
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from game.actions import GAME_ACTIONS, GameAction, actionId
from game.actions.actionBase import (
    ActionCommonBase,
    NoInitActionBase,
    TeamInteractionActionBase,
)
from game.viewsets.permissions import IsOrg


class ActionViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated, IsOrg)

    @staticmethod
    def type_info(outer_type: Type[Any]) -> dict[str, Any]:
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
                    ActionViewSet.type_info(subtype)
                    for subtype in typing.get_args(outer_type)
                ],
            }
        assert False, f"Not expected type {outer_type!r} (check if it's a ForwardRef)"

    @staticmethod
    def field_info(field: ModelField) -> dict[str, Any]:
        info = ActionViewSet.type_info(field.outer_type_)
        info["required"] = bool(field.required)
        if not field.required:
            info["default"] = field.get_default()
        return info

    @staticmethod
    def serialize_action_args(action: GameAction):
        assert isinstance(action.action, type)
        assert issubclass(action.action, ActionCommonBase)
        assert issubclass(action.action, (TeamInteractionActionBase, NoInitActionBase))

        args = {
            name: ActionViewSet.field_info(field)
            for name, field in action.argument.__fields__.items()
        }

        return {
            "id": actionId(action.action),
            "has_init": issubclass(action.action, TeamInteractionActionBase),
            "args": args,
        }

    def list(self, request: Request):
        return Response(
            [
                ActionViewSet.serialize_action_args(action)
                for action in GAME_ACTIONS.values()
            ]
        )
