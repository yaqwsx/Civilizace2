from __future__ import annotations

from abc import ABCMeta, abstractmethod
from decimal import Decimal
from math import ceil
from typing import Mapping, NamedTuple, Protocol, Type, TypeVar, Union

from pydantic import BaseModel, PrivateAttr
from typing_extensions import override

from game.actions.common import (
    ActionFailed,
    MessageBuilder,
    printResourceListForMarkdown,
)
from game.entities import Entities, MapTileEntity, Resource, TeamEntity
from game.state import Army, GameState, MapTile, TeamState


class ActionArgs(BaseModel):
    pass


class TeamActionArgs(ActionArgs):
    team: TeamEntity


class _TeamArgsProtocol(Protocol):
    @property
    def team(self) -> TeamEntity:
        ...


class _TileArgsProtocol(Protocol):
    @property
    def tile(self) -> MapTileEntity:
        ...


class _ArmyArgsProtocol(_TeamArgsProtocol, Protocol):
    @property
    def armyIndex(self) -> int:
        ...


# class TileActionArgs(ActionArgs):
#     tile: MapTileEntity

#     def tile_valid(self, state: GameState) -> bool:
#         return state.map.getTileById(self.tile.id) is not None

#     def tileState(self, state: GameState) -> MapTile:
#         tileState = state.map.getTileById(self.tile.id)
#         assert tileState is not None, "Tile is not valid"
#         return tileState

# class TeamArmyActionArgs(TeamActionArgs):
#     armyIndex: int

#     def army_valid(self, state: GameState) -> bool:
#         team_state = self.team_state(state)
#         return self.armyIndex in range(0, len(team_state.armies))

#     def army(self, state: GameState) -> Army:
#         team_state = self.team_state(state)
#         assert self.armyIndex in range(0, len(team_state.armies)), "Invalid army"
#         return team_state.armies[self.armyIndex]


TAction = TypeVar("TAction", bound="ActionCommonBase")
_TArgs = TypeVar("_TArgs", covariant=True)


class ActionProtocol(Protocol[_TArgs]):
    @property
    def args(self) -> _TArgs:
        ...

    @property
    def state(self) -> GameState:
        ...

    @property
    def entities(self) -> Entities:
        ...

    def _ensureStrong(self, condition: bool, message: str) -> None:
        ...


class ActionCommonBase(BaseModel, metaclass=ABCMeta):
    # Anything that is specified as PrivateAttr is not persistent. I know that
    # you like to have a lot of objects passed implicitly between the function,
    # instead of explicitly, so this is how you can do it.
    _state: GameState = PrivateAttr()  # We don't store state
    _entities: Entities = PrivateAttr()  # Nor entities
    _generalArgs: ActionArgs = PrivateAttr()  # Nor args
    _trace: MessageBuilder = PrivateAttr(default=MessageBuilder())
    # Nor traces. They always empty

    # This is mostly used such that user code logs messages
    # and wrappers inspect them.
    _errors: MessageBuilder = PrivateAttr(MessageBuilder())
    _warnings: MessageBuilder = PrivateAttr(MessageBuilder())
    _info: MessageBuilder = PrivateAttr(MessageBuilder())
    _notifications: dict[TeamEntity, list[str]] = PrivateAttr({})
    _scheduled_actions: list[ScheduledAction] = PrivateAttr([])

    # Private (and thus non-store args) have to start with underscore. Let's
    # give them normal names
    @property
    def state(self) -> GameState:
        return self._state

    @property
    def entities(self) -> Entities:
        return self._entities

    # Factory

    @classmethod
    def makeAction(
        cls: Type[TAction], state: GameState, entities: Entities, args: ActionArgs
    ) -> TAction:
        """The type of `args` has to match the `TAction`"""
        action = cls()
        action._state = state
        action._entities = entities
        action._generalArgs = args
        return action

    # Methods to be implemented by concrete actions

    @property
    @abstractmethod
    def args(self) -> ActionArgs:
        return self._generalArgs

    @property
    @abstractmethod
    def description(self) -> str:
        raise NotImplementedError()

    # Private API

    def _clearMessageBuilders(self) -> None:
        self._errors = MessageBuilder()
        self._warnings = MessageBuilder()
        self._info = MessageBuilder()
        self._notifications = {}

    def _addNotification(self, team: TeamEntity, message: str) -> None:
        if team not in self._notifications:
            self._notifications[team] = []
        self._notifications[team].append(message)

    def _scheduleAction(
        self, actionType: Type[NoInitActionBase], args: ActionArgs, delay_s: int
    ) -> ScheduledAction:
        action = ScheduledAction(actionType, args=args, delay_s=delay_s)
        self._scheduled_actions.append(action)
        return action

    def _ensure(self, condition: bool, message: str) -> bool:
        """
        Checks the condition, if it doesn't hold, return error
        """
        if not condition:
            self._errors += message
            return False
        return True

    def _ensureStrong(self, condition: bool, message: str) -> None:
        """
        Checks the condition, if it doesn't hold, raise ActionFailed
        """
        if not self._ensure(condition, message):
            raise ActionFailed(self._errors)

    def _ensureValid(self) -> None:
        if not self._errors.empty:
            raise ActionFailed(self._errors)

    def _generateActionResult(self) -> ActionResult:
        """Generates ActionResult from messages.

        Raises ActionFailed if any errors exist.

        Returns ActionResult with any warnings, infos and notifications.
        """
        if not self._errors.empty:
            raise ActionFailed(self._errors)

        return ActionResult(
            expected=self._warnings.empty,
            message=MessageBuilder(self._warnings, self._info).message,
            notifications=self._notifications,
            scheduledActions=self._scheduled_actions,
        )

    # Mixins

    def team_state(self: ActionProtocol[TeamActionArgs]) -> TeamState:
        assert (
            self.args.team in self.state.teamStates
        ), f"No team state for {self.args.team}"
        return self.state.teamStates[self.args.team]

    def _receiveResources(
        self: ActionProtocol[TeamActionArgs],
        resources: Mapping[Resource, Union[Decimal, int]],
        *,
        instantWithdraw: bool = False,
        excludeWork: bool = False,
    ) -> dict[Resource, Decimal]:
        # missing type intersection (Self & Action[TeamActionArgs]) to call team_state
        assert (
            self.args.team in self.state.teamStates
        ), f"No team state for {self.args.team}"
        team: TeamState = self.state.teamStates[self.args.team]
        withdrawing: dict[Resource, Decimal] = {}
        for resource, amount in resources.items():
            if excludeWork and resource == self.entities.work:
                continue
            if instantWithdraw and resource.isWithdrawable:
                withdrawing[resource] = Decimal(amount)
            else:
                if resource not in team.resources:
                    team.resources[resource] = Decimal(0)
                team.resources[resource] += amount

        if not instantWithdraw:
            assert withdrawing == {}
        return withdrawing

    def tile_state(self: ActionProtocol[_TileArgsProtocol]) -> MapTile:
        tile_state = self.state.map.getTileById(self.args.tile.id)
        assert tile_state is not None, f"No tile state for {self.args.tile}"
        return tile_state

    def army_state(self: ActionProtocol[_ArmyArgsProtocol]) -> Army:
        assert (
            self.args.team in self.state.teamStates
        ), f"No team state for {self.args.team}"
        team_state = self.state.teamStates[self.args.team]
        self._ensureStrong(
            self.args.armyIndex in range(0, len(team_state.armies)),
            f"Invalid army {self.args.armyIndex} for team {self.args.team.name}",
        )
        return team_state.armies[self.args.armyIndex]


class TeamInteractionActionBase(ActionCommonBase):
    """Represents Action which is a team interaction (has initiate phase)."""

    # The following fields are persistent

    paid: dict[Resource, Decimal] = {}

    # Public API

    def applyInitiate(self, *, ignore_cost: bool = False) -> str:
        """
        Voláno, když je třeba provést akci. Uvede herní stav do takového stavu,
        aby byl tým schopen házet kostkou a mohlo se přejít na commit.

        Returns: informace pro orgy o výběru materiálů.
        """
        assert not isinstance(self, NoInitActionBase)
        assert isinstance(self.args, TeamActionArgs)

        self._initiateCheck()
        self._ensureValid()

        if ignore_cost:
            return "Ignoruje se placení za akci"

        require = self._payResources(self.cost())

        return printResourceListForMarkdown(
            require,
            ceil,
            header="Vyberte od týmu materiály:",
            emptyHeader="Není potřeba vybírat od týmu žádný materiál",
        )

    def revertInitiate(self) -> str:
        """
        Vrátí efekty initiate (e.g. chyba orga)

        Returns: informace pro orgy o vrácení materiálů.
        """
        reward = self._revertPaidResources(instantWithdraw=True)
        return printResourceListForMarkdown(
            reward,
            ceil,
            header="Vraťte týmu materiály:",
            emptyHeader="Nevracíte týmu žádné materiály",
        )

    def commitThrows(self, *, throws: int, dots: int) -> ActionResult:
        """
        Voláno, když se doházelo.
        Zajistí promítnutí výsledků do stavu.
        Včetně toho, že tým naházel málo.
        """
        assert not isinstance(self, NoInitActionBase)
        self._clearMessageBuilders()

        self._initiateCheck()
        self._ensureValid()
        if not self._performThrow(throws, dots):
            reward = self._revertPaidResources(instantWithdraw=True, excludeWork=True)
            self._warnings += f"Házení kostkou neuspělo. Produkce byly týmu vráceny. O zaplacené materiály tým přišel a nic mu nevracíte."
            return self._generateActionResult()

        self._commitSuccessImpl()

        return self._generateActionResult()

    def commitSuccess(self) -> ActionResult:
        """
        Voláno, když chci automaticky vykonat akci bez házení.
        Zajistí promítnutí výsledků do stavu.

        Používá se v dry-run a případně u godmode.
        """
        assert not isinstance(self, NoInitActionBase)
        assert isinstance(self.args, TeamActionArgs)
        self._clearMessageBuilders()

        self._initiateCheck()
        self._ensureValid()

        self._commitSuccessImpl()

        return self._generateActionResult()

    # Methods to be implemented/overriden by concrete actions

    @property
    @abstractmethod
    @override
    def args(self) -> TeamActionArgs:
        args = super().args
        assert isinstance(args, TeamActionArgs)
        return args

    def cost(self) -> Union[dict[Resource, Decimal], dict[Resource, int]]:
        return {}

    def pointsCost(self) -> int:
        """
        Řekne, kolik teček je třeba hodit na kostce.
        Pokud vrátí 0, není třeba házet.
        """
        return 0

    def throwCost(self) -> int:
        """
        Řekne, kolik práce stojí jeden hod
        """
        return self.team_state().throwCost

    @abstractmethod
    def _commitSuccessImpl(self) -> None:
        raise NotImplementedError()

    def _initiateCheck(self) -> None:
        """Umožňuje akci neumožnit zadat initiate.

        Je potřeba vyhodit `ActionFailed`.
        Další informace se nepropíší.

        Je voláno před Initiate i před Commit.
        """
        pass

    # Private API

    def _performThrow(self, throws: int, dots: int) -> bool:
        """
        Performs throw, constructs a message in info and returns whether it was
        successful or not.
        """
        tState = self.team_state()
        pointsCost = self.pointsCost()
        workConsumed = throws * self.throwCost()
        workAvailable = tState.resources.get(self.entities.work, Decimal(0))

        tState.resources[self.entities.work] = max(
            Decimal(0), workAvailable - workConsumed
        )
        if workConsumed > workAvailable:
            self._warnings += (
                "Tým neměl dostatek práce (házel na jiném stanovišti?). "
                + "Akce neuspěla. Tým přišel o zaplacené zdroje."
            )
            return False
        if pointsCost > dots:
            self._warnings += (
                f"Tým nenaházel dostatek (chtěno {pointsCost}, naházeno {dots}). "
                + "Akce neuspěla. Tým přišel o zaplacené zdroje."
            )
            return False
        return True

    def _payResources(
        self, resources: Mapping[Resource, Union[Decimal, int]]
    ) -> dict[Resource, Decimal]:
        teamState = self.team_state()
        tokens = {}
        missing = {}
        for resource, amount in resources.items():
            if amount < 0:
                raise RuntimeError(
                    f"Pay amount cannot be negative ({amount}× {resource.name})"
                )
            if amount == 0:
                continue

            if resource.isWithdrawable:
                tokens[resource] = amount
                continue

            if resource not in teamState.resources:
                teamState.resources[resource] = Decimal(0)
            teamState.resources[resource] -= amount

            if teamState.resources[resource] < 0:
                missing[resource] = -teamState.resources[resource]
            if teamState.resources[resource] == 0:
                del teamState.resources[resource]

        self._ensureStrong(
            len(missing) == 0,
            MessageBuilder(
                "Tým nemá dostatek zdrojů. Chybí:",
                printResourceListForMarkdown(missing),
            ).message,
        )

        for resource, amount in resources.items():
            if resource not in self.paid:
                self.paid[resource] = Decimal(0)
            self.paid[resource] += amount

        return tokens

    def _revertPaidResources(
        self, *, instantWithdraw: bool = False, excludeWork: bool = False
    ) -> dict[Resource, Decimal]:
        """Gives back `self.paid` resources and empties them."""
        result = self._receiveResources(
            self.paid, instantWithdraw=instantWithdraw, excludeWork=excludeWork
        )
        self.paid = {}
        return result


class NoInitActionBase(ActionCommonBase):
    def commit(self) -> ActionResult:
        """
        Voláno pro vykonání akce. Zajistí promítnutí výsledků do stavu.
        """
        assert not isinstance(self, TeamInteractionActionBase)
        self._clearMessageBuilders()
        self._commitImpl()
        return self._generateActionResult()

    @abstractmethod
    def _commitImpl(self) -> None:
        raise NotImplementedError()


class ScheduledAction(NamedTuple):
    actionType: Type[NoInitActionBase]
    args: ActionArgs
    delay_s: int

    @property
    def actionName(self):
        return self.actionType.__name__


class ActionResult(BaseModel):
    expected: bool  # Was the result expected or unexpected
    message: str
    notifications: dict[TeamEntity, list[str]]
    scheduledActions: list[ScheduledAction]
