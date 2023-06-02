from typing import Any, Optional, Type, TypeVar

from django_enumfield import enum
from rest_framework import serializers


class IdRelatedField(serializers.SlugRelatedField):
    def to_internal_value(self, data):
        return data

    # TBA validate that the ID exists


class TextEnumField(serializers.ChoiceField):
    def to_representation(self, obj):
        if obj == "" and self.allow_blank:
            return obj
        return self._choices[obj].lower()

    def to_internal_value(self, data):
        # To support inserts with the value
        if data == "" and self.allow_blank:
            return ""

        for key, val in self._choices.items():
            if val.lower() == data:
                return key
        self.fail("invalid_choice", input=data)


class TextEnumSerializer(serializers.Field):
    def __init__(self, enum_type: Type[enum.Enum], *args, **kwargs):
        self.enum_type = enum_type
        super().__init__(*args, allow_null=True, **kwargs)

    def to_representation(self, obj: Optional[enum.Enum]) -> Optional[str]:
        return obj.name if obj is not None else None

    def to_internal_value(self, data: Optional[str]) -> Optional[enum.Enum]:
        if data is None or data == "":
            return None

        value = self.enum_type._member_map_.get(str(data))
        if value is not None:
            assert isinstance(value, self.enum_type)
            return value

        self.fail("invalid_choice", input=data)


TEnum = TypeVar("TEnum", bound=enum.Enum)


def enum_map(
    enum_type: Type[TEnum],
) -> dict[str, TEnum]:
    member_map: dict[str, Any] = enum_type._member_map_
    return member_map  # type: ignore
