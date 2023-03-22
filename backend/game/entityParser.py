from __future__ import annotations
from collections import Counter, deque
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
from typing import Any, Callable, Dict, ForwardRef, Iterable, List, Literal, Optional, Protocol, Tuple, Type, TypeVar, TypedDict, Union

from . import entities
from .entities import RESOURCE_VILLAGER, RESOURCE_WORK, TECHNOLOGY_START, GUARANTEED_IDS
from .entities import EntityId, Entities, Entity, EntityBase, EntityWithCost, TEntity
from .entities import Building, Die, MapTileEntity, NaturalResource, Org, Resource, ResourceType, Team, Tech, Vyroba

ReadOnlyEntityDict = Dict[EntityId, Entity] | frozendict[EntityId, Entity]

TModel = TypeVar("TModel", bound=BaseModel)

ALIASES: Dict[str, Callable[[ReadOnlyEntityDict], List[str]]] = {
    "die-any": lambda entities: [e.id for e in entities.values() if isinstance(e, Die)],
}

def str_to_bool(value: str) -> bool:
    """Convert a string representation of truth to true (1) or false (0).
    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    value = value.lower()
    if value in ('y', 'yes', 't', 'true', 'on', '1'):
        return True
    elif value in ('n', 'no', 'f', 'false', 'off', '0'):
        return False
    else:
        raise ValueError(f"Invalid boolean value '{value}'")

def unique(iter: Iterable[Any]) -> bool:
    return all(count <= 1 for count in Counter(iter).values())


class ParserError(Exception):
    def __init__(self, reason: str):
        self.reason = reason
    def __str__(self) -> str:
        return f"ParserError: {self.reason}"
    def __repr__(self) -> str:
        return str(self)

class ErrorHandler:
    def __init__(self, *, reporter: Callable[[str], None] = print, max_errs: int = 10, no_warn: bool = False):
        self.reporter = reporter
        self.max_errs = max_errs
        self.no_warn = no_warn
        self.error_msgs: List[str] = []
        self.warn_msgs: List[str] = []

    def success(self) -> bool:
        return len(self.error_msgs) == 0

    def errors_full(self) -> bool:
        return self.max_errs >= 0 and len(self.error_msgs) >= self.max_errs

    def error(self, error_str: str, *, ignore_max_errs: bool = False) -> None:
        self.error_msgs.append(error_str)
        if ignore_max_errs or not self.errors_full():
            self.reporter(f"  ERROR: {error_str}")

    # Ignores `self.max_errs`
    def validation_error(self, error: ValidationError) -> ParserError:
        model_name = error.model.__name__
        errors = error.errors()
        summary_str = f"Total {len(errors)} validation errors for {model_name}"
        self.error(summary_str, ignore_max_errs=True)
        for err in errors:
            arg_name = ' -> '.join(str(e) for e in err['loc'])
            err_msg = err['msg']
            err_type = err['type']
            err_ctx = ''.join(f'; {k}={v}' for k, v in err.get('ctx', {}).items())
            self.error(f"  Validation error for {model_name}, arg '{arg_name}': {err_msg} ({err_type}{err_ctx})", ignore_max_errs=True)
        return ParserError(summary_str)

    def warn(self, warn_str: str) -> None:
        self.warn_msgs.append(warn_str)
        if not self.no_warn:
            self.reporter(f"  WARN: {warn_str}")


class Delims:
    def __init__(self,
                 *,
                 list_delim: Optional[str] = ',',
                 tuple_delim: Optional[str] = ':',
                 ):
        assert list_delim != ""
        assert tuple_delim != ""
        self.list_delim = list_delim
        self.tuple_delim = tuple_delim

    def without_list_delim(self) -> Delims:
        return Delims(list_delim=None, tuple_delim=self.tuple_delim)
    def without_tuple_delim(self) -> Delims:
        return Delims(list_delim=self.list_delim, tuple_delim=None)


def value_preprocess(value: str) -> Optional[str]:
    value = value.strip()
    if value in ("", "-"):
        return None
    return value

def transform_lines_to_dicts(lines: List[List[str]],
                             preprocess: Callable[[str], Optional[str]] = value_preprocess,
                             *,
                             err_handler: ErrorHandler) -> List[Dict[str, str]]:
    assert len(lines) >= 1
    header, entity_lines = lines[0], lines[1:]

    if not unique(name for name in header if name != ""):
        err_handler.error(f"Duplicate header values in {tuple(header)}")

    return [{head: cell
                for head, cell in zip_longest(header, map(preprocess, line), fillvalue=None)
                    if head is not None and head != ""
                    if cell is not None
                }
            for line in entity_lines
           ]

def replace_alias(orig_value: str, replacing_values: Iterable[str], *, alias_pos: int, alias_len: int) -> Iterable[str]:
    assert alias_pos >= 0
    assert alias_len > 0
    assert len(orig_value) >= alias_pos + alias_len

    return iter(orig_value[:alias_pos] + repl_val + orig_value[alias_pos+alias_len:] for repl_val in replacing_values)

def fully_resolve_alias(values: Iterable[str],
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
        err_handler.warn(f"Alias {alias} has no replacing values when resolving {tuple(to_be_resolved)}")
    resolved = []
    while len(to_be_resolved) > 0:
        value = to_be_resolved.popleft()
        if (alias_pos := value.find(alias)) >= 0:
            to_be_resolved.extend(replace_alias(value, repl_values, alias_pos=alias_pos, alias_len=len(alias)))
        else:
            resolved.append(value)
    return resolved

def fully_resolve_aliases(values: Iterable[str], *, entities: ReadOnlyEntityDict, err_handler: ErrorHandler) -> Iterable[str]:
    for alias, repl_values in ALIASES.items():
        assert len(alias) > 0
        assert alias not in entities, f"Alias '{alias}' cannot be an Entity (type {type(entities[alias])})"
        values = fully_resolve_alias(values,
                                     alias=alias,
                                     replacing_values=lambda: repl_values(entities),
                                     err_handler=err_handler,
                                     )
    return values

def splitIterableField(arg: str,
                       *,
                       delim: str,
                       allowed: Callable[[str], bool] = lambda s: s != "",
                       entities: ReadOnlyEntityDict,
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
    raise ValueError(f"'{arg_casefold}' (from '{arg}') has to be one of {tuple(values)}")

def parseLiteralField(values: Tuple[Any, ...], arg: str) -> Any:
    tArgStrs = [(str(value).casefold(), value) for value in values]
    assert unique(name for name, _ in tArgStrs)
    return parseConstantFromDict(dict(tArgStrs), arg)

def parseEnum(cls: Type[Enum], arg: str) -> Enum:
    assert unique(map(str.casefold, cls._member_names_))
    member_map = {name.casefold(): value for name, value in cls._member_map_.items()}
    assert len(member_map) == len(cls._member_names_)
    return parseConstantFromDict(member_map, arg)

def parseTupleField(tArgs: Tuple[Type, ...],
                    arg: str,
                    *,
                    delims: Delims,
                    entities: ReadOnlyEntityDict,
                    err_handler: ErrorHandler,
                    ) -> Tuple[Any, ...]:
    assert len(tArgs) > 0
    assert delims.tuple_delim is not None, "No available delim to parse tuple of {tArgs} from '{arg}'"
    splitArg = list(splitIterableField(arg, delim=delims.tuple_delim, entities=entities, err_handler=err_handler))
    if len(splitArg) != len(tArgs):
        err_handler.error(f"Wrong number of parts in '{arg}' for '{tArgs}' (with delim '{delims.tuple_delim}')")
    return tuple(parseField(tArg, sArg, delims=delims.without_tuple_delim(), entities=entities, err_handler=err_handler)
                    for tArg, sArg in zip(tArgs, splitArg, strict=True))

def parseListField(tArg: Type,
                   arg: str,
                   *,
                   delims: Delims,
                   entities: ReadOnlyEntityDict,
                   err_handler: ErrorHandler,
                   ) -> List[Any]:
    assert delims.list_delim, "No available delim to parse list of {tArg} from '{arg}'"
    return [parseField(tArg, sArg, delims=delims.without_list_delim(), entities=entities, err_handler=err_handler)
                for sArg in splitIterableField(arg, delim=delims.list_delim, entities=entities, err_handler=err_handler)]

def parseDictField(tArgs: Tuple[Type, Type],
                   arg: str,
                   *,
                   delims: Delims,
                   entities: ReadOnlyEntityDict,
                   err_handler: ErrorHandler,
                   ) -> Dict[Any, Any]:
    assert delims.list_delim and delims.tuple_delim, "Not enough available delims to parse dict of {tArgs} from '{arg}'"
    pairValues = [parseTupleField(tArgs, pairValue, delims=delims.without_list_delim(), entities=entities, err_handler=err_handler)
                  for pairValue in splitIterableField(arg, delim=delims.list_delim, entities=entities, err_handler=err_handler)]
    if not unique(name for name, _ in pairValues):
        err_handler.error("Multiple keys in '{arg}' not allowed for dict of {tArgs} with delims '{delims.list_delim}' and '{delims.tuple_delim}'")
    return dict(pairValues)

def parseUnionAndOptionalField(tArgs: Tuple[Type, ...],
                               arg: str,
                               *,
                               delims: Delims,
                               entities: ReadOnlyEntityDict,
                               err_handler: ErrorHandler,
                               ) -> Any:
    if len(tArgs) == 2 and type(None) in tArgs: # Optional
        tArg, = iter(tArg for tArg in tArgs if tArg is not type(None))
        return parseField(tArg, arg, delims=delims, entities=entities, err_handler=err_handler)
    if str in tArgs:
        return arg
    raise NotImplementedError(f"Parsing Union of {tArgs} is not implemented")

def parseGenericField(cls: Type,
                      arg: str,
                      *,
                      delims: Delims,
                      entities: ReadOnlyEntityDict,
                      err_handler: ErrorHandler,
                      ) -> Any:
    origin = typing.get_origin(cls)
    tArgs = typing.get_args(cls)
    assert origin is not None

    if origin == Literal:
        return parseLiteralField(tArgs, arg)
    if origin == Union:  # Unions and Optionals
        return parseUnionAndOptionalField(tArgs, arg, delims=delims, entities=entities, err_handler=err_handler)

    if origin == tuple:
        return parseTupleField(tArgs, arg, delims=delims, entities=entities, err_handler=err_handler)
    if origin == list:
        tArg, = tArgs
        return parseListField(tArg, arg, delims=delims, entities=entities, err_handler=err_handler)
    if origin == dict:
        assert len(tArgs) == 2
        return parseDictField(tArgs, arg, delims=delims, entities=entities, err_handler=err_handler)

    raise NotImplementedError(f"Parsing {cls} (of type {type(cls)}) is not implemented")

def parseField(cls: Type,
               arg: str,
               *,
               delims: Delims = Delims(),
               entities: ReadOnlyEntityDict,
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
        return parseGenericField(cls, arg, delims=delims, entities=entities, err_handler=err_handler)

    if not isinstance(cls, type):
        raise NotImplementedError(f"Parsing '{cls}' of type '{type(cls)}' is not implemented")
    if issubclass(cls, Enum):
        return parseEnum(cls, arg)
    if issubclass(cls, EntityBase):
        entity = entities.get(arg)
        if entity is None:
            raise ParserError(f"Entity '{arg}' is not parsed yet")
        if not isinstance(entity, cls):
            raise ParserError(f"Entity '{arg}' is not '{cls}', instead is '{type(entity)}'")
        return entity
    raise NotImplementedError(f"Parsing {cls} is not implemented")


def parseFieldArgs(argTypes: Dict[str, Tuple[Type, bool]],
                   args: Dict[str, str],
                   *,
                   delims: Delims,
                   entities: ReadOnlyEntityDict,
                   err_handler: ErrorHandler,
                   ) -> Dict[str, Any]:
    unknown_fields = tuple(name for name in args if name not in argTypes)
    if len(unknown_fields) > 0:
        err_handler.warn(f"There are unknown fields: {unknown_fields} (expected one of {list(argTypes)})")

    parsed_args: Dict[str, Any] = {}
    for name, (fieldType, required) in argTypes.items():
        arg = args[name] if name in args else None

        if arg is None and required:
            needed_args = tuple(arg for arg in argTypes if argTypes[arg][1])
            err_handler.error(f"Field '{name}' is required, need {needed_args}, got {tuple(args)}")
        if arg is not None:
            try:
                parsed_args[name] = parseField(fieldType, arg, delims=delims, entities=entities, err_handler=err_handler)
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
            assert is_type(outer_type), f"Could not resolve field type of '{outer_type}' (from {field})"
            return outer_type
        except KeyError:
            assert False, f"Could not resolve forward ref of type '{outer_type}' (from {field})"
    assert False, f"Could not resolve field type of '{outer_type}' (from {field})"

def parseModel(cls: Type[TModel],
               args: Dict[str, str],
               *,
               entities: ReadOnlyEntityDict,
               delims: Delims=Delims(),
               err_handler: ErrorHandler,
               ) -> TModel:
    unknown_fields = tuple(name for name in args if name not in cls.__fields__)
    if len(unknown_fields) > 0:
        err_handler.warn(f"There are unknown fields for {cls}: {unknown_fields} (expected one of {list(cls.__fields__)})")

    arg_types = {name: (get_field_type(field), field.required == True) for name, field in cls.__fields__.items()}
    try:
        return cls.validate(parseFieldArgs(arg_types, args, delims=delims, entities=entities, err_handler=err_handler))
    except ValidationError as e:
        new_e: ParserError = err_handler.validation_error(e)
        raise new_e from e
    except (ParserError, ValueError) as e:
        reason = e.reason if isinstance(e, ParserError) else str(e)
        raise ParserError(f"{reason} (parsing model {cls} with id: {args.get('id')})") from e

def parseEntity(cls: Type[TEntity],
                args: Dict[str, str],
                *,
                allowed_prefixes: List[str],
                entities: ReadOnlyEntityDict,
                delims: Delims=Delims(),
                err_handler: ErrorHandler,
                ) -> TEntity:
    assert len(allowed_prefixes) > 0

    updateEntityArgs(cls, args, err_handler=err_handler)
    entity = parseModel(cls, args, entities=entities, delims=delims, err_handler=err_handler)
    if all(not entity.id.startswith(prefix) for prefix in allowed_prefixes):
        err_handler.error(f"Id '{entity.id}' does not start with any of {allowed_prefixes}")
    return entity

def updateEntityArgs(cls: Type[TEntity], args: Dict[str, str], *, err_handler: ErrorHandler) -> None:
    for name in list(args):
        if name.startswith('!'):
            args.pop(name)

    if issubclass(cls, EntityWithCost):
        if "cost" in args:
            err_handler.error(f"Don't use 'cost', use 'cost-work' and 'cost-other' instead")
        if "cost-work" not in args:
            err_handler.error(f"Expected 'cost-work' in {tuple(args)}")
        cost_work = args.pop("cost-work")
        cost_other = args.pop("cost-other", "")
        if RESOURCE_WORK in cost_other:
            err_handler.error(f"Don't use '{RESOURCE_WORK}' explicitly, use 'cost-work' instead")
        args["cost"] = f"{RESOURCE_WORK}:{cost_work},{cost_other}"

        if "points" in args and 'cost-points' in args:
                err_handler.error(f"Don't use both 'points' and 'cost-points', choose one")
        if "points" not in args:
            if "cost-points" in args:
                args["points"] = args.pop("cost-points")
            else:
                err_handler.error(f"Expected 'cost-points' or 'points' in {tuple(args)}")

    if issubclass(cls, Vyroba):
        assert issubclass(cls, EntityWithCost)
        cost_villager = args.pop("cost-villager", None)
        if RESOURCE_VILLAGER in args['cost']:
            err_handler.error(f"Don't use '{RESOURCE_VILLAGER}' explicitly, use 'cost-villager' instead")
        if cost_villager is not None:
            args["cost"] = f"{RESOURCE_VILLAGER}:{cost_villager},{args['cost']}"

    if issubclass(cls, MapTileEntity):
        if "id" in args:
            err_handler.error(f"Don't use 'id', id is computed automatically from 'index'")
        if "index" not in args:
            err_handler.error(f"Expected required value for 'index' {tuple(args)}")
        args['id'] = "map-tile" + args['index'].rjust(2, "0")


def parseSheet(entity_type: Type[TEntity],
               data: List[Dict[str, str]],
               *,
               allowed_prefixes: List[str],
               entities: ReadOnlyEntityDict,
               err_handler: ErrorHandler,
               ) -> Iterable[TEntity]:
    return iter(parseEntity(entity_type, args, allowed_prefixes=allowed_prefixes, entities=entities, err_handler=err_handler)
                    for args in data)



def add_tech_unlocks(tech: Tech,
                     unlock_args: Dict[str, str],
                     *,
                     entities: ReadOnlyEntityDict,
                     err_handler: ErrorHandler,
                     ) -> None:
    assert all(name.startswith("unlocks") for name in unlock_args)
    if "unlocks" in unlock_args:
        raise RuntimeError(f"Don't use 'unlocks', use 'unlocks-tech' and 'unlocks-other' instead")
    unknown_headers = tuple(name for name in unlock_args if name not in ("unlocks-tech", "unlocks-other"))
    if len(unknown_headers) > 0:
        raise RuntimeError(f"Unknown header values '{unknown_headers}', use 'unlocks-tech' and 'unlocks-other'")

    assert len(tech.unlocks) == 0

    unlocks_tech = unlock_args.get("unlocks-tech")
    if unlocks_tech is not None:
        tech.unlocks += parseField(List[Tuple[Tech, Die]], unlocks_tech, entities=entities, err_handler=err_handler)

    unlocks_other = unlock_args.get("unlocks-other")
    if unlocks_other is not None:
        tech.unlocks += parseField(List[Tuple[EntityWithCost, Die]], unlocks_other, entities=entities, err_handler=err_handler)


# TODO: remove
# def readRole(s: str) -> OrgRole:
#     s = s.lower()
#     if s == "org":
#         return OrgRole.ORG
#     if s == "super":
#         return OrgRole.SUPER
#     raise RuntimeError(f"{s} is not a valid role")

def createProduction(resource: Resource, prod_name: Optional[str], err_handler: ErrorHandler) -> Optional[Resource]:
    if resource.id.startswith("mat"):
        prod_prefix = "pro"
    elif resource.id.startswith("mge"):
        prod_prefix = "pge"
    else:
        if not resource.id.startswith("res"):
            err_handler.error(f"Resource has invalid id '{resource.id}'")
        prod_prefix = None

    if prod_prefix is None:
        return None

    id = prod_prefix + resource.id[len(prod_prefix):]

    if prod_name is None:
        err_handler.error(f"Resource material has to have a productionName ('{resource.id}')")
        prod_name = "MISSING PROD NAME"

    icon = None
    if resource.icon is not None:
        mat_icon_suff = 'a.svg'
        pro_icon_suff = 'b.svg'
        if not resource.icon.endswith(mat_icon_suff):
            err_handler.error(f"Resource material icon has to end with '{mat_icon_suff}'")
            resource.icon = "UNKNOWN_ICON_a.svg"
        icon = resource.icon[:-len(mat_icon_suff)] + pro_icon_suff

    return Resource(id=id, name=prod_name, typ=resource.typ, produces=resource, icon=icon)  # type: ignore



def checkGuaranteedIds(entities: ReadOnlyEntityDict, *, err_handler: ErrorHandler) -> None:
    for id in GUARANTEED_IDS:
        if id not in entities:
            err_handler.error(f"Missing guaranteed entity id '{id}'")


def checkUnlockConsistency(entities: Entities, *, err_handler: ErrorHandler) -> None:
    for entity in entities.values():
        if not isinstance(entity, EntityWithCost):
            continue
        for tech, die in entity.unlockedBy:
            assert tech is entities[tech.id]
            assert die in tech.allowedDie(entity)
            assert tech.unlocks.count((entity, die)) == 1
        if isinstance(entity, Tech):
            for unlocks_ent, die in entity.unlocks:
                assert isinstance(unlocks_ent, EntityWithCost)
                assert (entity, die) in unlocks_ent.unlockedBy
                assert unlocks_ent.unlockedBy.count((entity, die)) == 1

def checkUnlockedBy(entities: Entities, *, err_handler: ErrorHandler) -> None:
    for entity in entities.values():
        if not isinstance(entity, EntityWithCost):
            continue
        if entity.id == TECHNOLOGY_START:
            if len(entity.unlockedBy) > 0:
                err_handler.warn(f"{entity.id} ({entity.name}) has unlocking edge, but is START")
            continue
        if len(entity.unlockedBy) == 0:
            err_handler.warn(f"{entity.id} ({entity.name}) doesn't have unlocking edge")

def checkUnreachableByTech(entities: Entities, *, err_handler: ErrorHandler):
    visited_entities: Dict[EntityId, EntityWithCost] = {}
    changed = True
    while changed:
        changed = False
        for entity in entities.values():
            if not isinstance(entity, EntityWithCost):
                continue
            if entity.id in visited_entities:
                continue
            if all(tech.id in visited_entities for tech, _ in entity.unlockedBy):
                visited_entities[entity.id] = entity
                changed = True
    unreachable = [entity for entity in entities.values() if isinstance(entity, EntityWithCost) if entity not in visited_entities]
    if len(unreachable) > 0:
        err_handler.warn(f"There are unreachable entities with cost {unreachable}")


# def getEdgesFromField(entities: ReadOnlyEntityDict, field: str) -> List[Tuple[Entity, str]]:
#     chunks = [x.strip() for x in field.split(",")]
#     result = []
#     for chunk in chunks:
#         split = chunk.split(":")
#         assert len(split) == 2, "Invalid edge: " + chunk
#         targetId = split[0]
#         assert targetId in entities, "Unknown unlocking tech id \""\
#             + targetId \
#             + ("\"" if targetId[3] ==
#                 "-" else "\": Id is not exactly 3 symbols long")
#         targetEntity = entities[targetId]

#         die = split[1].strip()
#         if die == "die-any":
#             for die in DIE_IDS:
#                 result.append((targetEntity, die))
#             continue
#         assert die in DIE_IDS, "Unknown unlocking die id \"" + \
#             die + "\". Allowed dice are " + str(DIE_IDS)
#         result.append((targetEntity, die))
#     return result


# def checkMap(entities: Entities, err_handler: ErrorHandler) -> None:
#     if len(entities.teams) * 4 != len(entities.tiles):
#         err_handler.error("World size is wrong: \
#             There are {} tiles and {} teams \
#                 (expecting 4 tiles per team)".format(
#             len(entities.tiles),
#             len(entities.teams)))
#         return

#     tiles = entities.tiles
#     for i in range(len(tiles)):
#         count = sum(1 for x in tiles.values() if x.index == i)
#         if count > 1:
#             err_handler.error(
#                 "Tile index {} occured {} times".format(i, count))
#         if count < 1:
#             err_handler.error("Tile index {} missing".format(i))

class EntityParser():
    @staticmethod
    def parse(gs_data: Dict[str, List[List[str]]], *, err_handler: ErrorHandler = ErrorHandler()) -> Entities:
        assert len(err_handler.error_msgs) == 0
        assert len(err_handler.warn_msgs) == 0
        data = {tab: transform_lines_to_dicts(gs_data[tab], err_handler=err_handler) for tab in gs_data}

        entities: Dict[EntityId, Entity] = {}
        def add_entities(new_entities: Iterable[Entity]) -> None:
            for e in new_entities:
                if e.id in entities:
                    err_handler.error(f"Entity '{e.id}' is already in entities")
                    continue
                entities[e.id] = e

        add_entities(parseSheet(Die, data["dice"], allowed_prefixes=["die"], entities=entities, err_handler=err_handler))
        add_entities(parseSheet(ResourceType, data["resourceTypes"], allowed_prefixes=["typ"], entities=entities, err_handler=err_handler))
        res_prod_names = {args['id']: args['productionName'] for args in data["resources"] if 'productionName' in args}
        res_args = [{name: args[name] for name in args if name != 'productionName'} for args in data['resources']]
        for resource in parseSheet(Resource, res_args, allowed_prefixes=["res", "mat", "mge"], entities=entities, err_handler=err_handler):
            add_entities([resource])
            production = createProduction(resource, res_prod_names.get(resource.id), err_handler=err_handler)
            if production is not None:
                add_entities([production])

        tech_unlock_args = {args['id']: {name: args[name] for name in args if name.startswith("unlocks")} for args in data["techs"]}
        tech_args = [{name: args[name] for name in args if not name.startswith("unlocks")} for args in data["techs"]]
        add_entities(parseSheet(Tech, tech_args, allowed_prefixes=["tec"], entities=entities, err_handler=err_handler))

        add_entities(parseSheet(NaturalResource, data["naturalResources"], allowed_prefixes=["nat"], entities=entities, err_handler=err_handler))
        add_entities(parseSheet(MapTileEntity, data["tiles"], allowed_prefixes=["map"], entities=entities, err_handler=err_handler))

        add_entities(parseSheet(Building, data["buildings"], allowed_prefixes=["bui"], entities=entities, err_handler=err_handler))
        add_entities(parseSheet(Vyroba, data["vyrobas"], allowed_prefixes=["vyr"], entities=entities, err_handler=err_handler))

        add_entities(parseSheet(Team, data["teams"], allowed_prefixes=["tym"], entities=entities, err_handler=err_handler))
        add_entities(parseSheet(Org, data["orgs"], allowed_prefixes=["org"], entities=entities, err_handler=err_handler))

        for tech_id, unlock_args in tech_unlock_args.items():
            assert tech_id in entities
            tech = entities[tech_id]
            assert isinstance(tech, Tech)
            add_tech_unlocks(tech, unlock_args, entities=entities, err_handler=err_handler)

        # TODO: compute EntityWithCost.unlockedBy (and check it was empty if required)
        # TODO: update tech.unlocks from vyroba.unlockedBy
        # TODO: assert not reward.isGeneric, f'Vyroba cannot reward generic resource "{reward}"'
        # TODO: building required features have to be natural
        # TODO: check Team starting tile (or make if Entity)


        # TODO work = self.entities["res-prace"]
        # TODO obyvatel = self.entities["res-obyvatel"]
        # TODO culture = self.entities["res-kultura"]
        # TODO obyvatel.produces = work
        # TODO culture.produces = obyvatel

        entities_result = Entities(entities.values())

        # checkUnlockedBy() # TODO
        # checkUnlockConsistency() # TODO
        # checkUnreachableByTech() # TODO
        # checkGuaranteedIds() # TODO
        # checkMap(entities_result) # TODO

        return entities_result

    @staticmethod
    def load(filename: str | PathLike[str], *, err_handler = ErrorHandler()):
        with open(filename) as file:
            data = json.load(file)

        typed_data: Dict[str, List[List[str]]] = data
        # Check the correct type of the json data
        assert isinstance(typed_data, dict)
        for k, v in typed_data.items():
            assert isinstance(k, str)
            assert isinstance(v, list)
            for inner in v:
                assert isinstance(inner, list)
                assert all(isinstance(x, str) for x in inner)

        return EntityParser.parse(typed_data, err_handler=err_handler)
