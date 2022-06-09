import contextlib
from decimal import Decimal
from math import ceil
from typing import Any, Callable, Dict, Generator, List, Optional, Set, Tuple

from pydantic import BaseModel, PrivateAttr
from game.actions.common import ActionFailed, MessageBuilder

from game.entities import DieId, Entities, Resource, Team
from game.state import GameState, TeamState, printResourceListForMarkdown

class ActionArgs(BaseModel):
    pass

class ActionResult(BaseModel):
    expected: bool # Was the result expected or unexpected
    message: str
    notifications: Dict[Team, List[str]]={}

class ActionInterface(BaseModel):
    _state: GameState = PrivateAttr()        # We don't store state
    _entities: Entities = PrivateAttr()      # Nor entities
    _generalArgs: Any = PrivateAttr()        # Nor args

    description: Optional[str]               # This field should be filled by the initiate step

    # Private (and thus non-store args) have to start with underscore. Let's
    # give them normal names
    @property
    def state(self):
        return self._state

    @property
    def entities(self):
        return self._entities

    @property
    def team(self):
        if hasattr(self._generalArgs, "team"):
            return self._generalArgs.team.id
        return None


    def diceRequirements(self) -> Tuple[Set[DieId], int]:
        """
        Řekne, kolik teček je třeba hodit na jedné z kostek. Pokud vrátí prázdný
        seznam, není třeba házet.
        """
        raise NotImplementedError("You have to implement this")

    def throwCost(self) -> int:
        """
        Řekne, kolik práce stojí jeden hod
        """
        raise NotImplementedError("You have to implement this")

    def applyInitiate(self) -> ActionResult:
        """
        Voláno, když je třeba provést akci. Uvede herní stav do takového stavu,
        aby byl tým schopen házet kostkou a mohlo se přejít na commit.
        """
        raise NotImplementedError("You have to implement this")


    def applyCommit(self, throws: int, dots: int) -> ActionResult:
        """
        Voláno, když je je doházeno (i když se neházelo). Zajistí promítnutí
        výsledků do stavu. Včetně toho, že tým naházel málo.
        """
        raise NotImplementedError("You have to implement this")

    def requiresDelayedEffect(self) -> int:
        """
        Říká, jestli akce má odložený efekt a za kolik sekund.
        """
        raise NotImplementedError("You have to implement this")

    def applyDelayedEffect(self) -> ActionResult:
        """
        Voláno přesně, když má proběhnout odložený efekt. Zpráva se zde nikam
        nepromítne a měla by být prázdná.
        raise NotImplementedError("You have to implement this")
        """

    def applyDelayedReward(self) -> ActionResult:
        """
        Provede propsání odměny týmů do stavu. Děje se když tým přijde se
        směnkou.
        """
        raise NotImplementedError("You have to implement this")

    def revertInitiate(self) -> ActionResult:
        """
        Vrátí efekty initiate
        """
        raise NotImplementedError("You have to implement this")

def makeAction(cls, state, entities, args):
     action = cls()
     action._state = state
     action._entities = entities
     action._generalArgs = args
     return action

class ActionBase(ActionInterface):
    # Anything that is specified as PrivateAttr is not persistent. I know that
    # you like to have a lot of objects passed implicitly between the function,
    # instead of explicitly, so this is how you can do it.
    #
    # For example, initiate can reset these fields, call some functions that will
    # use them and then initiate can inspect them.
    _errors: MessageBuilder = PrivateAttr()
    _warnings: MessageBuilder = PrivateAttr()
    _info: MessageBuilder = PrivateAttr()
    _notifications: Dict[Team, List[str]] = PrivateAttr()

    # The following fields are persistent:
    paid: Dict[Resource, Decimal] = {}

    # Private API below

    @property
    def teamState(self) -> Optional[TeamState]:
        if hasattr(self._generalArgs, "team"):
            return self.state.teamStates[self._generalArgs.team]
        return None

    def _setupPrivateAttrs(self):
        self._errors = MessageBuilder()
        self._warnings = MessageBuilder()
        self._info = MessageBuilder()
        self._notifications = {}

    def _performThrow(self, throws: int, dots: int) -> bool:
        """
        Performs throw, constructs a message in info and returns whether it was
        successful or not.
        """
        tState = self.teamState
        if throws == 0 or tState is None:
            assert dots == 0
            return True
        _, dotsRequired = self.diceRequirements()
        workConsumed = throws * self.teamState.throwCost
        workAvailable = tState.work

        tState.resources[self.entities.work] = max(0, tState.resources[self.entities.work] - workConsumed)
        if workConsumed > workAvailable:
            self._warnings.add("Tým neměl dostatek práce (házel na jiném stanovišti?). " + \
                          "Akce nebude provedena.")
            return False
        if dotsRequired > dots:
            self._warnings.add(f"Tým nenaházel dostatek (chtěno {dotsRequired}, hodil {dots}" + \
                            "Akce nebude provedena.")
            return False
        return True

    def _ensure(self, condition: bool, message: str) -> None:
        """
        Checks the condition, if it doesn't hold, yield error
        """
        if not condition:
            self._errors.add(message)
            return False
        return True

    def _ensureStrong(self, condition: bool, message: str) -> None:
        """
        Checks the condition, if it doesn't hold, yield error
        """
        if not condition:
            self._errors.add(message)
            raise ActionFailed(self._errors)

    @property
    def _ensureValid(self) -> None:
        if not self._errors.empty:
            raise ActionFailed(self._errors)

    @contextlib.contextmanager
    def _startBothLists(self, header: str) -> Generator[Callable[[str], None], None, None]:
        with    self._info.startList(header) as addILine, \
                self.error.startList(header) as addELine:
            def addLine(*args, **kwargs):
                addILine(*args, **kwargs)
                addELine(*args, **kwargs)
            yield addLine


    def payResources(self, resources: Dict[Resource, Decimal]) -> Dict[Resource, Decimal]:
        team = self.teamState
        tokens = {}
        missing = {}
        for resource, amount in resources.items():
            if resource.isTracked:
                team.resources[resource] = team.resources.get(resource, 0) - amount
                if resource.id == "res-obyvatel":
                    team.addEmployees(amount)
                if team.resources[resource] < 0:
                    missing[resource] = -team.resources[resource]
            else:
                tokens[resource] = amount

        if missing != {}:
            raise ActionFailed(f"Tým nemá dostatek zdrojů. Chybí: [[{printResourceListForMarkdown(missing)}]]")

        return tokens


    def receiveResources(self, resources: Dict[Resource, Decimal], instantWithdraw: bool = False) -> Dict[Resource, Decimal]:
        team = self.teamState
        storage = {}
        for resource, amount in resources.items():
            if resource.isTracked:
                team.resources[resource] = team.resources.get(resource, 0) + amount
            else:
                storage[resource] = amount
        if instantWithdraw:
            return storage
        for resource, amount in storage.items():
            amount = team.storage.get(resource, 0) + amount
            if amount > team.storageCapacity and resource.id != "mat-zbrane":
                amount = team.storageCapacity
            team.storage[resource] = amount
        return {}


    def diceRequirements(self) -> Tuple[Set[DieId], int]:
        return (set(), 0)

    def throwCost(self) -> int:
        return self.teamState.throwCost


    def requiresDelayedEffect(self) -> int:
        return 0

    def costSubstituted(self):
        cost = self.cost()
        if hasattr(self._generalArgs, "genericsMapping"):
            mapping = self._generalArgs.genericsMapping
            cost = {(mapping[generic] if generic in mapping else generic): amount for generic, amount in cost.items()}
        return cost


    def applyInitiate(self) -> ActionResult:
        cost = self.costSubstituted()
        message = ""
        if len(cost) > 0:
            require = self.payResources(cost)
            message = f"Vyberte od týmu materiály:{printResourceListForMarkdown(require, ceil)}"

        return ActionResult(
            expected=True,
            message=message)


    def revertInitiate(self) -> ActionResult:
        cost = self.cost()
        reward = self.receiveResources(cost, instantWithdraw=True)
        message = f"Vraťte týmu materiály:{printResourceListForMarkdown(reward, ceil)}"

        return ActionResult(
            expected=True,
            message=message)


    def cancelAction(self):
        cost = self.costSubstituted()
        reward = self.receiveResources(cost, instantWithdraw=True)


    def generateActionResult(self):
        if not self._errors.empty:
            raise ActionFailed(self._errors)
        if not self._warnings.empty:
            return ActionResult(
                expected=False,
                message="**" + self._warnings.message + "**\n\n" + self._info.message,
                notifications=self._notifications)
        return ActionResult(
            expected=True,
            message=self._info.message,
            notifications=self._notifications)


    def applyCommit(self, throws: int=0, dots: int=0) -> ActionResult:
        self._setupPrivateAttrs()
        throwingSucc = self._performThrow(throws, dots)
        if not throwingSucc:
            self.cancelAction()
            self._warnings += f"Házení kostkou neuspělo. Produkce byly týmu vráceny. O zaplacené materiály tým přišel a nic mu nevracíte."
            return self.generateActionResult()

        self._commitImpl()
        if self.requiresDelayedEffect() == 0:
            self._applyDelayedEffect()
            self._applyDelayedReward()

        return self.generateActionResult()


    def applyDelayedEffect(self) -> ActionResult:
        self._setupPrivateAttrs()
        self._applyDelayedEffect()
        return self.generateActionResult()


    def applyDelayedReward(self) -> ActionResult:
        self._setupPrivateAttrs()
        self._applyDelayedReward()
        return self.generateActionResult()


    def _applyDelayedEffect(self):
        pass


    def _applyDelayedReward(self):
        pass

