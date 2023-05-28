from __future__ import annotations
from collections import Counter, deque
from contextlib import contextmanager
import decimal
from decimal import Decimal
from enum import Enum
from frozendict import frozendict
from itertools import zip_longest
import json
from os import PathLike
import pydantic
from pydantic import BaseModel, ValidationError
import typing
from typing import (
    Any,
    Callable,
    Dict,
    ForwardRef,
    Iterable,
    List,
    Literal,
    Mapping,
    NamedTuple,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from . import entities
from .entities import RESOURCE_VILLAGER, RESOURCE_WORK, TECHNOLOGY_START, GUARANTEED_IDS
from .entities import (
    EntityId,
    Entities,
    Entity,
    EntityBase,
    EntityWithCost,
    UserEntity,
)
from .entities import (
    Building,
    Die,
    MapTileEntity,
    NaturalResource,
    OrgEntity,
    Resource,
    ResourceType,
    TeamEntity,
    Tech,
    Vyroba,
)
from .state import WorldState
from .util import TEntity, unique


TModel = TypeVar("TModel", bound=BaseModel)

# Aliases duplicate the strings that they appear in
# Notes:
# - They work on substring substitution
# - BE CAREFUL when the alias can be a substring of any value
# - List is used to ensure the desired order of aliases
# - They duplicate only in iterables
# - They duplicate in the OUTER-MOST iterable (NOT in the inner-most)
#     - (Implementation reason - it's not needed to be otherwise)
#     - If e.g. Map[_, Set[<Aliasable>]] is required, this will have to be implemented
ALIASES: List[Tuple[str, Callable[[Mapping[EntityId, Entity]], List[str]]]] = [
    (
        "die-any",
        lambda entities: [e.id for e in entities.values() if isinstance(e, Die)],
    ),
]


def str_to_bool(value: str) -> bool:
    """Convert a string representation of truth to true (1) or false (0).
    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    value = value.lower()
    if value in ("y", "yes", "t", "true", "on", "1"):
        return True
    elif value in ("n", "no", "f", "false", "off", "0"):
        return False
    else:
        raise ValueError(f"Invalid boolean value '{value}'")


class ParserError(Exception):
    def __init__(self, reason: str):
        self.reason = reason

    def __str__(self) -> str:
        return f"ParserError: {self.reason}"

    def __repr__(self) -> str:
        return str(self)


class ErrorHandler:
    def __init__(
        self,
        *,
        reporter: Callable[[str], None] = print,
        max_errs: int = 10,
        no_warn: bool = False,
    ) -> None:
        self.reporter = reporter
        self.max_errs = max_errs
        self.no_warn = no_warn
        self.error_msgs: List[str] = []
        self.warn_msgs: List[str] = []
        self.context_list = []

    def success(self) -> bool:
        return len(self.error_msgs) == 0

    def check_success(
        self, name: str, result_reporter: Callable[[str], None] = print
    ) -> None:
        msgs = [("error", len(self.error_msgs)), ("warn", len(self.warn_msgs))]
        msgs = [(msg_type, count) for msg_type, count in msgs if count > 0]

        summary_msg = f"Parsing {name} {'SUCCESS' if self.success() else 'FAILED'}"
        if len(msgs) > 0:
            msgs_summary = ", ".join(
                f"{count} {msg_type}{'' if count == 1 else 's'}"
                for msg_type, count in msgs
            )
            summary_msg += f": {msgs_summary}"

        result_reporter(summary_msg)
        if not self.success():
            raise ParserError(summary_msg)

    def errors_full(self) -> bool:
        return self.max_errs >= 0 and len(self.error_msgs) >= self.max_errs

    def check_max_errs_reached(self) -> None:
        if self.errors_full():
            raise ParserError(
                f"Parsing FAILED: Stopping parsing, encountered max number of errors (max={self.max_errs})"
            )

    @property
    def context_str(self):
        return f"[{':'.join(self.context_list)}]"

    @contextmanager
    def add_context(self, context: str):
        try:
            self.context_list.append(context)
            yield
        finally:
            self.pop_context(context)

    def pop_context(self, expected_context: Optional[str] = None) -> None:
        assert len(self.context_list) > 0
        old_context = self.context_list.pop()
        assert (
            old_context == expected_context
        ), f"Expected context '{expected_context}' but got '{old_context}' {self.context_str}"

    def warn(self, warn_str: str) -> None:
        self.warn_msgs.append(warn_str)
        if not self.no_warn:
            self.reporter(f"  {self.context_str} WARN: {warn_str}")

    def error(self, error_str: str, *, ignore_max_errs: bool = False) -> None:
        self.error_msgs.append(error_str)
        self.reporter(f"  {self.context_str} ERROR: {error_str}")
        if not ignore_max_errs:
            self.check_max_errs_reached()

    # Ignores `self.max_errs`
    def validation_error(self, error: ValidationError) -> ParserError:
        model_name = error.model.__name__
        errors = error.errors()
        summary_str = f"Total {len(errors)} validation errors for {model_name}"
        self.error(summary_str, ignore_max_errs=True)
        for err in errors:
            arg_name = " -> ".join(str(e) for e in err["loc"])
            err_msg = err["msg"]
            err_type = err["type"]
            err_ctx = "".join(f"; {k}={v}" for k, v in err.get("ctx", {}).items())
            self.error(
                f"  Validation error for {model_name}, arg '{arg_name}': {err_msg} ({err_type}{err_ctx})",
                ignore_max_errs=True,
            )
        self.check_max_errs_reached()
        raise ParserError(
            f"Parsing FAILED: Encountered validation error, so far encountered {len(self.error_msgs)} errors"
        )


class Delims:
    def __init__(
        self,
        *,
        list_delims: List[str] = [",", ";"],
        tuple_delims: List[str] = [":", "/"],
    ):
        assert all(delim != "" for delim in list_delims)
        assert all(delim != "" for delim in tuple_delims)
        self.list_delims = list_delims
        self.tuple_delims = tuple_delims

    def next_list_delim(self) -> Optional[str]:
        return None if len(self.list_delims) == 0 else self.list_delims[0]

    def next_tuple_delim(self) -> Optional[str]:
        return None if len(self.tuple_delims) == 0 else self.tuple_delims[0]

    def without_list_delim(self) -> Delims:
        assert len(self.list_delims) > 0
        return Delims(list_delims=self.list_delims[1:], tuple_delims=self.tuple_delims)

    def without_tuple_delim(self) -> Delims:
        assert len(self.tuple_delims) > 0
        return Delims(list_delims=self.list_delims, tuple_delims=self.tuple_delims[1:])


def value_preprocess(value: str) -> Optional[str]:
    value = value.strip()
    if value in ("", "-"):
        return None
    return value


def transform_lines_to_dicts(
    lines: List[List[str]],
    preprocess: Callable[[str], Optional[str]] = value_preprocess,
    *,
    err_handler: ErrorHandler,
) -> List[Dict[str, str]]:
    assert len(lines) >= 1
    header, entity_lines = lines[0], lines[1:]

    if not unique(name for name in header if name != ""):
        err_handler.error(f"Duplicate header values in {tuple(header)}")

    return [
        {
            head: cell
            for head, cell in zip_longest(header, map(preprocess, line), fillvalue=None)
            if head is not None and head != ""
            if cell is not None
        }
        for line in entity_lines
    ]


def replace_alias(
    orig_value: str, replacing_values: Iterable[str], *, alias_pos: int, alias_len: int
) -> Iterable[str]:
    assert alias_pos >= 0
    assert alias_len > 0
    assert len(orig_value) >= alias_pos + alias_len

    return iter(
        orig_value[:alias_pos] + repl_val + orig_value[alias_pos + alias_len :]
        for repl_val in replacing_values
    )


def fully_resolve_alias(
    values: Iterable[str],
    *,
    alias: str,
    replacing_values: Callable[[], List[str]],
    err_handler: ErrorHandler,
) -> Iterable[str]:
    assert len(alias) > 0
    to_be_resolved = deque(values)
    if all(value.find(alias) < 0 for value in to_be_resolved):
        return to_be_resolved

    repl_values = replacing_values()
    if len(repl_values) == 0:
        err_handler.warn(
            f"Alias {alias} has no replacing values when resolving {tuple(to_be_resolved)}"
        )
    resolved = []
    while len(to_be_resolved) > 0:
        value = to_be_resolved.popleft()
        if (alias_pos := value.find(alias)) >= 0:
            to_be_resolved.extend(
                replace_alias(
                    value, repl_values, alias_pos=alias_pos, alias_len=len(alias)
                )
            )
        else:
            resolved.append(value)
    return resolved


def fully_resolve_aliases(
    values: Iterable[str],
    *,
    entities: Mapping[EntityId, Entity],
    err_handler: ErrorHandler,
) -> Iterable[str]:
    for alias, repl_values in ALIASES:
        assert len(alias) > 0
        assert (
            alias not in entities
        ), f"Alias '{alias}' cannot be an Entity (type {type(entities[alias])})"
        values = fully_resolve_alias(
            values,
            alias=alias,
            replacing_values=lambda: repl_values(entities),
            err_handler=err_handler,
        )
    return values


def splitIterableField(
    arg: str,
    *,
    delim: str,
    allowed: Callable[[str], bool] = lambda s: s != "",
    entities: Mapping[EntityId, Entity],
    err_handler: ErrorHandler,
) -> Iterable[str]:
    assert delim != ""
    result = list(map(str.strip, arg.split(delim)))
    if not allowed(result[-1]):
        result.pop()
    if not all(map(allowed, result)):
        err_handler.error(f"Value '{arg}' not allowed as iterable with delim '{delim}'")
    return fully_resolve_aliases(result, entities=entities, err_handler=err_handler)


def parseConstantFromDict(values: Dict[str, Any], arg: str) -> Any:
    assert all(name == name.casefold() for name in values)
    arg_casefold = arg.casefold()
    if arg_casefold in values:
        return values[arg_casefold]
    raise ValueError(
        f"'{arg_casefold}' (from '{arg}') has to be one of {tuple(values)}"
    )


def parseLiteralField(values: Tuple[Any, ...], arg: str) -> Any:
    tArgStrs = [(str(value).casefold(), value) for value in values]
    assert unique(name for name, _ in tArgStrs)
    return parseConstantFromDict(dict(tArgStrs), arg)


def parseEnum(cls: Type[Enum], arg: str) -> Enum:
    assert unique(map(str.casefold, cls._member_names_))
    member_map = {name.casefold(): value for name, value in cls._member_map_.items()}
    assert len(member_map) == len(cls._member_names_)
    return parseConstantFromDict(member_map, arg)


def parseTupleField(
    tArgs: Tuple[Type[Any], ...],
    arg: str,
    *,
    delims: Delims,
    entities: Mapping[EntityId, Entity],
    err_handler: ErrorHandler,
) -> Tuple[Any, ...]:
    assert len(tArgs) > 0
    delim = delims.next_tuple_delim()
    assert delim, f"No available delim to parse tuple of {tArgs} from '{arg}'"
    next_delims = delims.without_tuple_delim()
    splitArg = list(
        splitIterableField(arg, delim=delim, entities=entities, err_handler=err_handler)
    )
    if len(splitArg) != len(tArgs):
        err_handler.error(
            f"Wrong number of parts in '{arg}' for '{tArgs}' (with delim '{delim}')"
        )
    return tuple(
        parseField(
            tArg, sArg, delims=next_delims, entities=entities, err_handler=err_handler
        )
        for tArg, sArg in zip(tArgs, splitArg, strict=True)
    )


def parseListField(
    tArg: Type,
    arg: str,
    *,
    delims: Delims,
    entities: Mapping[EntityId, Entity],
    err_handler: ErrorHandler,
) -> List[Any]:
    delim = delims.next_list_delim()
    assert delim, f"No available delim to parse list of {tArg} from '{arg}'"
    next_delims = delims.without_list_delim()
    return [
        parseField(
            tArg, sArg, delims=next_delims, entities=entities, err_handler=err_handler
        )
        for sArg in splitIterableField(
            arg, delim=delim, entities=entities, err_handler=err_handler
        )
    ]


def parseDictField(
    tArgs: Tuple[Type, Type],
    arg: str,
    *,
    delims: Delims,
    entities: Mapping[EntityId, Entity],
    err_handler: ErrorHandler,
) -> Dict[Any, Any]:
    delim = delims.next_list_delim()
    assert (
        delim and delims.next_tuple_delim()
    ), f"Not enough available delims to parse dict of {tArgs} from '{arg}'"
    next_delims = delims.without_list_delim()
    pairValues = [
        parseTupleField(
            tArgs,
            pairValue,
            delims=next_delims,
            entities=entities,
            err_handler=err_handler,
        )
        for pairValue in splitIterableField(
            arg, delim=delim, entities=entities, err_handler=err_handler
        )
    ]
    if not unique(name for name, _ in pairValues):
        err_handler.error(
            f"Multiple keys in '{arg}' not allowed for dict of {tArgs} with delims '{delim}' and '{next_delims.next_tuple_delim()}'"
        )
    return dict(pairValues)


def parseUnionAndOptionalField(
    tArgs: Tuple[Type, ...],
    arg: str,
    *,
    delims: Delims,
    entities: Mapping[EntityId, Entity],
    err_handler: ErrorHandler,
) -> Any:
    if len(tArgs) == 2 and type(None) in tArgs:  # Optional
        (tArg,) = iter(tArg for tArg in tArgs if tArg is not type(None))
        return parseField(
            tArg, arg, delims=delims, entities=entities, err_handler=err_handler
        )
    if str in tArgs:
        return arg
    raise NotImplementedError(f"Parsing Union of {tArgs} is not implemented")


def parseGenericField(
    cls: Type,
    arg: str,
    *,
    delims: Delims,
    entities: Mapping[EntityId, Entity],
    err_handler: ErrorHandler,
) -> Any:
    origin = typing.get_origin(cls)
    tArgs = typing.get_args(cls)
    assert origin is not None

    if origin == Literal:
        return parseLiteralField(tArgs, arg)
    if origin == Union:  # Unions and Optionals
        return parseUnionAndOptionalField(
            tArgs, arg, delims=delims, entities=entities, err_handler=err_handler
        )

    if origin == tuple:
        return parseTupleField(
            tArgs, arg, delims=delims, entities=entities, err_handler=err_handler
        )
    if origin == list:
        (tArg,) = tArgs
        return parseListField(
            tArg, arg, delims=delims, entities=entities, err_handler=err_handler
        )
    if origin == dict:
        assert len(tArgs) == 2
        return parseDictField(
            tArgs, arg, delims=delims, entities=entities, err_handler=err_handler
        )

    raise NotImplementedError(f"Parsing {cls} (of type {type(cls)}) is not implemented")


def parseField(
    cls: Type,
    arg: str,
    *,
    delims: Delims = Delims(),
    entities: Mapping[EntityId, Entity],
    err_handler: ErrorHandler,
) -> Any:
    assert isinstance(arg, str)
    if cls == str:
        return arg
    if cls == int:
        return int(arg)
    if cls == Decimal:
        try:
            return Decimal(arg)
        except decimal.InvalidOperation:
            raise ValueError(f"invalid literal for Decimal: '{arg}'")
    if cls == bool:
        return str_to_bool(arg)
    if typing.get_origin(cls) is not None:
        return parseGenericField(
            cls, arg, delims=delims, entities=entities, err_handler=err_handler
        )

    if not isinstance(cls, type):
        raise NotImplementedError(
            f"Parsing '{cls}' of type '{type(cls)}' is not implemented"
        )
    if issubclass(cls, Enum):
        return parseEnum(cls, arg)
    if issubclass(cls, EntityBase):
        entity = entities.get(arg)
        if entity is None:
            raise ParserError(f"Entity '{arg}' is not parsed yet")
        if not isinstance(entity, cls):
            raise ParserError(
                f"Entity '{arg}' is not '{cls}', instead is '{type(entity)}'"
            )
        return entity
    raise NotImplementedError(f"Parsing {cls} is not implemented")


def parseFieldArgs(
    argTypes: Mapping[str, Tuple[Type, bool]],
    args: Mapping[str, str],
    *,
    delims: Delims,
    entities: Mapping[EntityId, Entity],
    err_handler: ErrorHandler,
) -> Dict[str, Any]:
    unknown_fields = tuple(name for name in args if name not in argTypes)
    if len(unknown_fields) > 0:
        err_handler.warn(
            f"There are unknown fields: {unknown_fields} (expected one of {list(argTypes)})"
        )

    parsed_args: Dict[str, Any] = {}
    for name, (fieldType, required) in argTypes.items():
        arg = args[name] if name in args else None

        if arg is None and required:
            needed_args = tuple(arg for arg in argTypes if argTypes[arg][1])
            err_handler.error(
                f"Field '{name}' is required, need {needed_args}, got {tuple(args)}"
            )
        if arg is not None:
            try:
                parsed_args[name] = parseField(
                    fieldType,
                    arg,
                    delims=delims,
                    entities=entities,
                    err_handler=err_handler,
                )
            except (ValueError, ParserError) as e:
                err_handler.error(str(e))
    return parsed_args


def get_field_type(field: pydantic.fields.ModelField) -> Type:
    def is_type(value: Any) -> bool:
        return isinstance(value, type) or typing.get_origin(value) is not None

    outer_type = field.outer_type_
    if is_type(outer_type):
        return outer_type
    if isinstance(outer_type, ForwardRef):
        try:
            outer_type = eval(outer_type.__forward_code__, entities.__dict__)
            assert is_type(
                outer_type
            ), f"Could not resolve field type of '{outer_type}' (from {field})"
            return outer_type
        except KeyError:
            assert (
                False
            ), f"Could not resolve forward ref of type '{outer_type}' (from {field})"
    assert False, f"Could not resolve field type of '{outer_type}' (from {field})"


def parseModel(
    cls: Type[TModel],
    args: Mapping[str, str],
    *,
    entities: Mapping[EntityId, Entity],
    delims: Delims = Delims(),
    err_handler: ErrorHandler,
) -> TModel:
    unknown_fields = tuple(name for name in args if name not in cls.__fields__)
    if len(unknown_fields) > 0:
        err_handler.warn(
            f"There are unknown fields for {cls}: {unknown_fields} (expected one of {list(cls.__fields__)})"
        )

    arg_types = {
        name: (get_field_type(field), field.required == True)
        for name, field in cls.__fields__.items()
    }
    try:
        return cls.validate(
            parseFieldArgs(
                arg_types,
                args,
                delims=delims,
                entities=entities,
                err_handler=err_handler,
            )
        )
    except ValidationError as e:
        new_e: ParserError = err_handler.validation_error(e)
        raise new_e from e
    except (ParserError, ValueError) as e:
        reason = e.reason if isinstance(e, ParserError) else str(e)
        raise ParserError(
            f"{reason} (parsing model {cls} with id: {args.get('id')})"
        ) from e


def parseEntity(
    cls: Type[TEntity],
    args: Dict[str, str],
    *,
    allowed_prefixes: List[str],
    entities: Mapping[EntityId, Entity],
    delims: Delims = Delims(),
    err_handler: ErrorHandler,
) -> TEntity:
    assert len(allowed_prefixes) > 0
    old_err_count = len(err_handler.error_msgs)
    with err_handler.add_context(f"entity(id='{args.get('id', None)}')"):
        updateEntityArgs(cls, args, err_handler=err_handler)
        entity = parseModel(
            cls, args, entities=entities, delims=delims, err_handler=err_handler
        )
        if all(not entity.id.startswith(prefix) for prefix in allowed_prefixes):
            err_handler.error(
                f"Id '{entity.id}' does not start with any of {allowed_prefixes}"
            )

    if (err_count := len(err_handler.error_msgs) - old_err_count) > 0:
        err_handler.error(
            f"New {err_count} errors while parsing entity '{entity.id} ({entity.name})'"
        )
    return entity


def updateEntityArgs(
    cls: Type[TEntity], args: Dict[str, str], *, err_handler: ErrorHandler
) -> None:
    for name in list(args):
        if name.startswith("!"):
            args.pop(name)

    if issubclass(cls, EntityWithCost):
        if "cost" in args:
            err_handler.error(
                f"Don't use 'cost', use 'cost-work' and 'cost-other' instead"
            )
        if "cost-work" not in args:
            err_handler.error(f"Expected 'cost-work' in {tuple(args)}")
            return
        cost_work = args.pop("cost-work")
        cost_other = args.pop("cost-other", "")
        if RESOURCE_WORK in cost_other:
            err_handler.error(
                f"Don't use '{RESOURCE_WORK}' explicitly, use 'cost-work' instead"
            )
        args["cost"] = f"{RESOURCE_WORK}:{cost_work},{cost_other}"

        if "points" in args and "cost-points" in args:
            err_handler.error(f"Don't use both 'points' and 'cost-points', choose one")
        if "points" not in args:
            if "cost-points" in args:
                args["points"] = args.pop("cost-points")
            else:
                err_handler.error(
                    f"Expected 'cost-points' or 'points' in {tuple(args)}"
                )

    if issubclass(cls, Vyroba):
        assert issubclass(cls, EntityWithCost)
        cost_villager = args.pop("cost-villager", None)
        if RESOURCE_VILLAGER in args["cost"]:
            err_handler.error(
                f"Don't use '{RESOURCE_VILLAGER}' explicitly, use 'cost-villager' instead"
            )
        if cost_villager is not None:
            args["cost"] = f"{RESOURCE_VILLAGER}:{cost_villager},{args['cost']}"

    def tileIdFromName(name: str) -> EntityId:
        return f"map-tile-{name}"

    if issubclass(cls, MapTileEntity):
        if "id" in args:
            err_handler.error(
                f"Don't use 'id', id is computed automatically from 'index'"
            )
        if "name" not in args:
            err_handler.error(f"Expected required value for 'name' {tuple(args)}")
            return
        args["id"] = tileIdFromName(args["name"])

    if issubclass(cls, TeamEntity):
        if "homeTile" in args:
            err_handler.error(f"Don't use 'homeTile', use 'homeTileName' instead")
        if "homeTileName" not in args:
            err_handler.error(
                f"Expected required value for 'homeTileName' {tuple(args)}"
            )
            return
        homeTileName = args.pop("homeTileName")
        args["homeTile"] = tileIdFromName(homeTileName)


def parseSheet(
    entity_type: Type[TEntity],
    data: List[Dict[str, str]],
    *,
    allowed_prefixes: List[str],
    entities: Mapping[EntityId, Entity],
    err_handler: ErrorHandler,
) -> Iterable[TEntity]:
    return iter(
        parseEntity(
            entity_type,
            args,
            allowed_prefixes=allowed_prefixes,
            entities=entities,
            err_handler=err_handler,
        )
        for args in data
    )


def add_tech_unlocks(
    tech: Tech,
    unlock_args: Dict[str, str],
    *,
    entities: Mapping[EntityId, Entity],
    err_handler: ErrorHandler,
) -> None:
    assert all(name.startswith("unlocks") for name in unlock_args)
    if "unlocks" in unlock_args:
        raise RuntimeError(
            f"Don't use 'unlocks', use 'unlocks-tech' and 'unlocks-other' instead"
        )
    unknown_headers = tuple(
        name for name in unlock_args if name not in ("unlocks-tech", "unlocks-other")
    )
    if len(unknown_headers) > 0:
        raise RuntimeError(
            f"Unknown header values '{unknown_headers}', use 'unlocks-tech' and 'unlocks-other'"
        )

    assert len(tech.unlocks) == 0

    unlocks_tech = unlock_args.get("unlocks-tech")
    if unlocks_tech is not None:
        tech.unlocks += parseField(
            List[Tech],
            unlocks_tech,
            entities=entities,
            err_handler=err_handler,
        )

    unlocks_other = unlock_args.get("unlocks-other")
    if unlocks_other is not None:
        tech.unlocks += parseField(
            List[EntityWithCost],
            unlocks_other,
            entities=entities,
            err_handler=err_handler,
        )


def add_hardcoded_values(
    entities: Dict[str, Entity], *, err_handler: ErrorHandler
) -> None:
    work = entities[RESOURCE_WORK]
    obyvatel = entities[RESOURCE_VILLAGER]
    assert isinstance(work, Resource)
    assert isinstance(obyvatel, Resource)
    obyvatel.produces = work


def production_prefix(
    resource_id: EntityId, *, err_handler: ErrorHandler
) -> Optional[str]:
    if resource_id.startswith("mat"):
        return "pro"
    if resource_id.startswith("mge"):
        return "pge"
    if resource_id.startswith("res"):
        return None

    err_handler.error(f"Resource has invalid id '{resource_id}'")
    return None


def createProduction(
    resource: Resource, prod_name: Optional[str], err_handler: ErrorHandler
) -> Optional[Resource]:
    prod_prefix = production_prefix(resource.id, err_handler=err_handler)
    if prod_prefix is None:
        return None

    id = prod_prefix + resource.id[len(prod_prefix) :]

    if prod_name is None:
        err_handler.error(
            f"Resource material has to have a productionName ('{resource.id}')"
        )
        prod_name = "MISSING PROD NAME"

    icon = None
    if resource.icon is not None:
        mat_icon_suff = "a.svg"
        pro_icon_suff = "b.svg"
        if not resource.icon.endswith(mat_icon_suff):
            err_handler.error(
                f"Resource material icon has to end with '{mat_icon_suff}'"
            )
            resource.icon = "UNKNOWN_ICON_a.svg"
        icon = resource.icon[: -len(mat_icon_suff)] + pro_icon_suff

    return Resource(id=id, name=prod_name, typ=resource.typ, produces=resource, icon=icon)  # type: ignore


def with_productions(
    resources: Iterable[Resource],
    res_prod_names: Mapping[EntityId, str],
    *,
    err_handler: ErrorHandler,
) -> Iterable[Resource]:
    for resource in resources:
        yield resource
        production = createProduction(
            resource, res_prod_names.get(resource.id), err_handler=err_handler
        )
        if production is not None:
            yield production


def synchronizeUnlocks(entities: Dict[str, Entity]) -> None:
    for entity in entities.values():
        if isinstance(entity, EntityWithCost):
            for tech in entity.unlockedBy:
                tech.unlocks.append(entity)
            entity.unlockedBy.clear()

    for tech in entities.values():
        if isinstance(tech, Tech):
            for entity in tech.unlocks:
                entity.unlockedBy.append(tech)


def checkGuaranteedIds(
    entities: Mapping[EntityId, Entity], *, err_handler: ErrorHandler
) -> None:
    for id in GUARANTEED_IDS:
        if id not in entities:
            err_handler.error(f"Missing guaranteed entity id '{id}'")
        elif not isinstance(entities[id], GUARANTEED_IDS[id]):
            err_handler.error(
                f"Guaranteed entity '{id}' has wrong type, expected '{GUARANTEED_IDS[id]}' but got '{type(entities[id])}'"
            )


def checkEntitiesHaveUnlockedBy(
    entities: Entities, *, err_handler: ErrorHandler
) -> None:
    for entity in entities.values():
        if not isinstance(entity, EntityWithCost):
            continue
        if entity.id == TECHNOLOGY_START:
            if len(entity.unlockedBy) > 0:
                err_handler.warn(
                    f"{entity.id} ({entity.name}) has unlocking edge, but is START"
                )
            continue
        if len(entity.unlockedBy) == 0:
            err_handler.warn(f"{entity.id} ({entity.name}) doesn't have unlocking edge")


# TODO: check - and probably change
def checkUnreachableByTech(entities: Entities, *, err_handler: ErrorHandler):
    visited_entities: Set[EntityWithCost] = set([entities.techs[TECHNOLOGY_START]])
    changed = True
    while changed:
        changed = False
        for entity in entities.values():
            if not isinstance(entity, EntityWithCost):
                continue
            if entity in visited_entities:
                continue
            if any(tech in visited_entities for tech in entity.unlockedBy):
                visited_entities.add(entity)
                changed = True
    unreachable = [
        entity.id
        for entity in entities.values()
        if isinstance(entity, EntityWithCost)
        if entity not in visited_entities
    ]
    if len(unreachable) > 0:
        err_handler.warn(f"There are unreachable entities with cost {unreachable}")


def check_teams_have_different_home_tiles(
    entities: Entities, *, err_handler: ErrorHandler
) -> None:
    if not unique(team.homeTile for team in entities.teams.values()):
        err_handler.error(f"There are multiple teams with the same home tile")


def checkMap(entities: Entities, *, err_handler: ErrorHandler) -> None:
    if len(entities.tiles) != 4 * len(entities.teams):
        err_handler.error(
            f"World size is wrong: \
            There are {len(entities.tiles)} tiles \
            and {len(entities.teams)} teams (expecting 4 tiles per team)"
        )

    expected_index_range = range(len(entities.tiles))
    tile_indices = Counter(tile.index for tile in entities.tiles.values())

    missing_indices = tuple(
        index for index in expected_index_range if tile_indices[index] == 0
    )
    out_of_bound_indices = tuple(
        index for index in tile_indices if index not in expected_index_range
    )
    duplicate_indices = {
        index: count for index, count in tile_indices.items() if count > 1
    }

    if len(out_of_bound_indices) > 0:
        err_handler.error(
            f"Out of bound tile indices: {out_of_bound_indices}", ignore_max_errs=True
        )
    if len(duplicate_indices) > 0:
        err_handler.error(
            f"Duplicate tile indices: {duplicate_indices}", ignore_max_errs=True
        )
    if len(missing_indices) > 0:
        err_handler.error(
            f"Missing tile indices: {missing_indices}", ignore_max_errs=True
        )

    err_handler.check_max_errs_reached()


def checkUsersHaveLogins(entities: Entities, *, err_handler: ErrorHandler) -> None:
    for user in entities:
        if not isinstance(user, UserEntity):
            continue
        if user.username is None or user.username == "":
            err_handler.error(f"User '{user}' cannot have blank username")
        if user.password is None or user.password == "":
            err_handler.error(f"User '{user}' cannot have blank password")


class EntityParser:
    @staticmethod
    def parse_entities(
        data: Mapping[str, List[Dict[str, str]]],
        *,
        err_handler: ErrorHandler = ErrorHandler(),
        result_reporter: Optional[Callable[[str], None]] = None,
    ) -> Entities:
        assert len(err_handler.error_msgs) == 0

        if result_reporter is None:
            result_reporter = err_handler.reporter

        entities_map: Dict[EntityId, Entity] = {}

        def add_entities(new_entities: Iterable[Entity]) -> None:
            for e in new_entities:
                if e.id in entities_map:
                    err_handler.error(f"Entity '{e.id}' is already in entities")
                    continue
                entities_map[e.id] = e

        with err_handler.add_context("dice"):
            add_entities(
                parseSheet(
                    Die,
                    data["dice"],
                    allowed_prefixes=["die"],
                    entities=entities_map,
                    err_handler=err_handler,
                )
            )
        with err_handler.add_context("resourceTypes"):
            add_entities(
                parseSheet(
                    ResourceType,
                    data["resourceTypes"],
                    allowed_prefixes=["typ"],
                    entities=entities_map,
                    err_handler=err_handler,
                )
            )
        with err_handler.add_context("resources"):
            res_args = [
                {name: args[name] for name in args if name != "productionName"}
                for args in data["resources"]
            ]
            resources = parseSheet(
                Resource,
                res_args,
                allowed_prefixes=["res", "mat", "mge"],
                entities=entities_map,
                err_handler=err_handler,
            )
            res_prod_names = {
                args["id"]: args["productionName"]
                for args in data["resources"]
                if "productionName" in args
            }
            add_entities(
                with_productions(resources, res_prod_names, err_handler=err_handler)
            )

        with err_handler.add_context("techs"):
            tech_unlock_args = {
                args["id"]: {
                    name: args[name] for name in args if name.startswith("unlocks")
                }
                for args in data["techs"]
            }
            tech_args = [
                {name: args[name] for name in args if not name.startswith("unlocks")}
                for args in data["techs"]
            ]
            add_entities(
                parseSheet(
                    Tech,
                    tech_args,
                    allowed_prefixes=["tec"],
                    entities=entities_map,
                    err_handler=err_handler,
                )
            )

        with err_handler.add_context("naturalResources"):
            add_entities(
                parseSheet(
                    NaturalResource,
                    data["naturalResources"],
                    allowed_prefixes=["nat"],
                    entities=entities_map,
                    err_handler=err_handler,
                )
            )
        with err_handler.add_context("tiles"):
            add_entities(
                parseSheet(
                    MapTileEntity,
                    data["tiles"],
                    allowed_prefixes=["map"],
                    entities=entities_map,
                    err_handler=err_handler,
                )
            )

        with err_handler.add_context("buildings"):
            add_entities(
                parseSheet(
                    Building,
                    data["buildings"],
                    allowed_prefixes=["bui"],
                    entities=entities_map,
                    err_handler=err_handler,
                )
            )
        with err_handler.add_context("vyrobas"):
            add_entities(
                parseSheet(
                    Vyroba,
                    data["vyrobas"],
                    allowed_prefixes=["vyr"],
                    entities=entities_map,
                    err_handler=err_handler,
                )
            )

        with err_handler.add_context("teams"):
            add_entities(
                parseSheet(
                    TeamEntity,
                    data["teams"],
                    allowed_prefixes=["tym"],
                    entities=entities_map,
                    err_handler=err_handler,
                )
            )
        with err_handler.add_context("orgs"):
            add_entities(
                parseSheet(
                    OrgEntity,
                    data["orgs"],
                    allowed_prefixes=["org"],
                    entities=entities_map,
                    err_handler=err_handler,
                )
            )

        with err_handler.add_context("tech unlocks"):
            for tech_id, unlock_args in tech_unlock_args.items():
                assert tech_id in entities_map
                tech = entities_map[tech_id]
                assert isinstance(tech, Tech)
                add_tech_unlocks(
                    tech, unlock_args, entities=entities_map, err_handler=err_handler
                )

        checkGuaranteedIds(entities_map, err_handler=err_handler)
        add_hardcoded_values(entities_map, err_handler=err_handler)

        synchronizeUnlocks(entities_map)

        entities = Entities(entities_map.values())
        with err_handler.add_context("final checks"):
            check_teams_have_different_home_tiles(entities, err_handler=err_handler)
            checkUnreachableByTech(entities, err_handler=err_handler)
            checkMap(entities, err_handler=err_handler)
            checkUsersHaveLogins(entities, err_handler=err_handler)

        err_handler.check_success("Entities", result_reporter=result_reporter)
        assert err_handler.success()
        return entities

    @staticmethod
    def parse(
        gs_data: Dict[str, List[List[str]]],
        *,
        err_handler: ErrorHandler = ErrorHandler(),
        result_reporter: Optional[Callable[[str], None]] = None,
    ) -> Entities:
        assert len(err_handler.error_msgs) == 0
        assert len(err_handler.warn_msgs) == 0

        data = frozendict(
            {
                tab: transform_lines_to_dicts(gs_data[tab], err_handler=err_handler)
                for tab in gs_data
            }
        )

        return EntityParser.parse_entities(
            data, err_handler=err_handler, result_reporter=result_reporter
        )

    @staticmethod
    def load_gs_data(filename: str | PathLike[str]) -> Dict[str, List[List[str]]]:
        with open(filename) as file:
            data = json.load(file)

        # Check the correct type of the json data
        assert isinstance(data, dict)
        for k, v in data.items():
            assert isinstance(k, str)
            assert isinstance(v, list)
            for inner in v:
                assert isinstance(inner, list)
                assert all(isinstance(x, str) for x in inner)
        return data

    @staticmethod
    def load(filename: str | PathLike[str], *, err_handler=ErrorHandler()) -> Entities:
        data = EntityParser.load_gs_data(filename)
        return EntityParser.parse(data, err_handler=err_handler)
