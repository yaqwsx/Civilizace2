import contextlib
from decimal import Decimal
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple

from pydantic import BaseModel, PrivateAttr
from game.actions.actionBase import ActionArgs
from game.actions.common import MessageBuilder

from game.entities import DieId, Entities, Resource, Team
from game.state import GameState, TeamState

class ActionFailed(Exception):
    """
    Expects a pretty (markdown-formatted) message. This message will be seen
    by the user. That is raise ActionFailed(message)
    """
    def __init__(self, message):
        if isinstance(message, MessageBuilder):
            super().__init__(message.message)
        super().__init__(message)

class ActionResultNew(BaseModel):
    expected: bool # Was the result expected or unexpected
    message: str
    notifications: Dict[Team, List[str]]={}

class ActionInterface(BaseModel):
    _state: GameState = PrivateAttr()        # We don't store state
    _entities: Entities = PrivateAttr()      # Nor entities
    _generalArgs: Any = PrivateAttr()        # Nor args

    # Private (and thus non-store args) have to start with underscore. Let's
    # give them normal names
    @property
    def state(self):
        return self._state

    @property
    def entities(self):
        return self._entities

    def __init__(self, state: GameState, entities: Entities, args: Any) -> None:
        super().__init__()
        self._state = state
        self._entities = entities
        self._generalArgs = args

    def diceRequirements(self) -> Tuple[List[DieId], int]:
        """
        Řekne, kolik teček je třeba hodit na jedné z kostek. Pokud vrátí prázdný
        seznam, není třeba házet.
        """
        raise NotImplementedError("You have to implement this")

    def applyInitiate(self) -> ActionResultNew:
        """
        Voláno, když je třeba provést akci. Uvede herní stav do takového stavu,
        aby byl tým schopen házet kostkou a mohlo se přejít na commit.
        """
        raise NotImplementedError("You have to implement this")


    def applyCommit(self, throws: int, dots: int) -> ActionResultNew:
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

    def applyDelayedEffect(self) -> ActionResultNew:
        """
        Voláno přesně, když má proběhnout odložený efekt. Zpráva se zde nikam
        nepromítne a měla by být prázdná.
        raise NotImplementedError("You have to implement this")
        """

    def applyDelayedReward(self) -> ActionResultNew:
        """
        Provede propsání odměny týmů do stavu. Děje se když tým přijde se
        směnkou.
        """
        raise NotImplementedError("You have to implement this")

    def revertInitiate(self) -> ActionResultNew:
        """
        Vrátí efekty initiate
        """
        raise NotImplementedError("You have to implement this")

class ActionBaseNew(ActionInterface):
    # Anything that is specified as PrivateAttr is not persistent. I know that
    # you like to have a lot of objects passed implicitly between the function,
    # instead of explicitly, so this is how you can do it.
    #
    # For example, initiate can reset these fields, call some functions that will
    # use them and then initiate can inspect them.
    _errors: MessageBuilder = PrivateAttr()
    _info: MessageBuilder = PrivateAttr()

    # The following fields are persistent:
    paid: Dict[Resource, Decimal] = {}


    # Private API below

    @property
    def teamState(self) -> Optional[TeamState]:
        assert hasattr(self._generalArgs, "team")
        return self.state.teamStates[self._generalArgs.team]

    def _setupPrivateAttrs(self):
        self._errors = MessageBuilder()
        self._info = MessageBuilder()

    def _initiateImpl(self) -> None:
        raise NotImplementedError("You hve to implement this")

    def _performThrow(self, throws: int, dots: int) -> bool:
        """
        Performs throw, constructs a message in info and returns whether it was
        successful or not.
        """
        if throws == 0:
            assert dots == 0
            return True
        tState = self.teamState
        _, dotsRequired = self.diceRequirements()
        workConsumed = throws * 5 # TBA Use computed price

        tState.resources[self.entities.work] = max(0, tState.resources[self.entities.work] - workConsumed)
        if workConsumed > tState.work:
            self._info.add("Tým neměl dostatek práce (házel na jiném stanovišti?). " + \
                          "Akce nebude provedena.")
            return False
        if dotsRequired > dots:
            self._info.add(f"Tým nenaházel dostatek (chtěno {dotsRequired}, hodil {dots}" + \
                            "Akce nebude provedena.")
            return False

    def _ensure(self, condition: bool, message: str) -> None:
        """
        Checks the condition, if it doesn't hold, yield error
        """
        if not condition:
            self._errors.add(message)

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

    def _makePayment(self, what: Dict[Resource, Decimal]) -> bool:
        """
        Pay resources (during initiate). Productions are deduced and store for
        the possibility to revert them. Materials are formatted into the
        message. When there are resources missing, they are formatted into
        errors.
        """
        if len(what) == 0:
            return
        fail = False
        tState = self.teamState
        productions = {r: a for r, a in what.items() if r.isProduction}
        materials = {r: a for r, a in what.items() if r.isMaterial}

        with self._errors.startList("## Týmu chybějí následující zdroje:") as addLine:
            for r, required in productions:
                available = tState.resources.get(r, 0)
                if available < required:
                    addLine(f"[[{r.id}|{required - available}]]")
                    fail = True
        if fail:
            return False

        with self._info.startList("## Tým zaplatí:") as addLine:
            for r, required in productions.items():
                addLine(f"[[{r.id}|{required}]]")
                tState.resources[r] -= required
                self.paid[r] = self.paid.get(r, 0) + required
        with self._info.startList("## Od týmu ještě vyberte:") as addLine:
            for r, required in materials.items():
                self.paid[r] = self.paid.get(r, 0) + required
                addLine(f"[[{r.id}|{required}]]")
        return True

    def _revertPaymentProductions(self) -> None:
        """
        Reverts all productions from payments via _makePayment. Adds message
        both to info and error
        """
        productions = {r: a for r, a in self.paid.items() if r.isProduction}
        if len(productions) == 0:
            return
        tState = self.teamState
        with self._startBothLists("## Týmu se vrací:") as addLine:
            for r, a in productions.items():
                tState.resources[r] = tState.resources.get(r, 0) + a
                addLine(f"[[{r.id}|{a}]]")

    def _revertPaymentMaterials(self) -> None:
        """
        Reverts all material from payments via _makePayment. Adds message
        both to info and error
        """
        materials = {r: a for r, a in self.paid.items() if r.isMaterial}
        with self._startBothLists("## Týmu vraťte:") as addLine:
            for r, a in materials.items():
                addLine(f"[[{r.id}|{a}]]")

    def applyInitiate(self) -> ActionResultNew:
        self._setupPrivateAttrs()
        self._initiateImpl()
        if not self._errors.empty:
            raise ActionFailed(self._errors)
        return ActionResultNew(
            expected=True,
            message=self._info.message)


    def applyCommit(self, throws: int, dots: int) -> ActionResultNew:
        self._setupPrivateAttrs()
        throwingSucc = self._performThrow(throws, dots)
        if not throwingSucc:
            self._revertPaymentProductions()
            return ActionResultNew(
                expected=False,
                message=self._info.message
            )

        expected = self._commitImpl(self)

        if not self._errors.empty:
            raise ActionFailed(self._errors)
        return ActionResultNew(
            expected=expected,
            message=self._info.message)

    def revertInitiate(self) -> ActionResultNew:
        self._setupPrivateAttrs()
        self._revertPaymentProductions()
        self._revertPaymentMaterials()
        return ActionResultNew(
            expected=True,
            message=self._info.message)
