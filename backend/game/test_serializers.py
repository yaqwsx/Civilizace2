from decimal import Decimal
import json
from typing import Any, Optional
import pydantic
from game.entities import Entities
from game import serializers


class MyTestBaseModel(pydantic.BaseModel):
    value_int: int = 4
    value_str: str
    value_decimal: Decimal
    value_opt_bool: Optional[bool] = True
    other: Optional["MyTestBaseModel"] = None


def test_serialize():
    class TestCase:
        def __init__(self, /, value: Any, expected: Any, expected_json: str) -> None:
            self.value = value
            self.expected = expected
            self.expected_json = expected_json

    tests: list[TestCase] = [
        TestCase(
            value=MyTestBaseModel(
                value_str="zcx",
                value_decimal=Decimal("98.7"),
                other=MyTestBaseModel(
                    value_str="asd", value_decimal=Decimal("0.111"), value_opt_bool=None
                ),
            ),
            expected={
                "value_int": 4,
                "value_str": "zcx",
                "value_decimal": "98.7",
                "value_opt_bool": True,
                "other": {
                    "value_int": 4,
                    "value_str": "asd",
                    "value_decimal": "0.111",
                    "value_opt_bool": None,
                    "other": None,
                },
            },
            expected_json=r'{"value_int": 4, "value_str": "zcx", "value_decimal": "98.7", "value_opt_bool": true, "other": {"value_int": 4, "value_str": "asd", "value_decimal": "0.111", "value_opt_bool": null, "other": null}}',
        ),
    ]

    for test in tests:
        ser = serializers.Serializer()
        ser_value = ser.serialize(test.value)
        assert ser_value == test.expected
        ser_str = json.dumps(ser_value)
        assert ser_str == test.expected_json


def test_deserialize():
    class TestCase:
        def __init__(
            self,
            /,
            json_str: str,
            expected_any: Any,
            expected: Any,
            cls: Optional[type] = None,
            entities: Optional[Entities] = None,
        ) -> None:
            self.json_str = json_str
            self.expected_any = expected_any
            self.expected = expected
            self.cls = cls if cls is not None else type(expected)
            self.entities = entities

    tests: list[TestCase] = [
        TestCase(
            json_str=r'{"value_int": 4, "value_str": "zcx", "value_decimal": "98.7", "value_opt_bool": true, "other": {"value_int": 4, "value_str": "asd", "value_decimal": "0.111", "value_opt_bool": null, "other": null}}',
            expected_any={
                "value_int": 4,
                "value_str": "zcx",
                "value_decimal": "98.7",
                "value_opt_bool": True,
                "other": {
                    "value_int": 4,
                    "value_str": "asd",
                    "value_decimal": "0.111",
                    "value_opt_bool": None,
                    "other": None,
                },
            },
            expected=MyTestBaseModel(
                value_str="zcx",
                value_decimal=Decimal("98.7"),
                other=MyTestBaseModel(
                    value_str="asd", value_decimal=Decimal("0.111"), value_opt_bool=None
                ),
            ),
        ),
    ]

    for test in tests:
        deser = serializers.Deserializer(entities=test.entities)
        deser_any = json.loads(test.json_str)
        assert deser_any == test.expected_any
        deser_value = deser.deserialize(test.cls, deser_any)
        assert isinstance(deser_value, test.cls)
        assert deser_value == test.expected
