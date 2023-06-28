import traceback

from typing_extensions import override

from game.actions.actionBase import ActionArgs, NoInitActionBase
from game.actions.common import ActionFailed, MessageBuilder
from game.gameGlue import stateDeserialize, stateSerialize
from game.state import GameState


class GodModeArgs(ActionArgs):
    original: GameState
    new: GameState


class GodModeAction(NoInitActionBase):
    @property
    @override
    def args(self) -> GodModeArgs:
        assert isinstance(self._generalArgs, GodModeArgs)
        return self._generalArgs

    @property
    @override
    def description(self) -> str:
        return "Godmode Action"

    @override
    def _commitImpl(self) -> None:
        currentState = stateDeserialize(
            GameState, stateSerialize(self.state), self.entities
        )
        originalState = self.args.original
        newState = self.args.new

        if newState.world != originalState.world:
            if self._ensure(
                originalState.world == currentState.world,
                "Stavy světa se liší, nemůžu aplikovat změny",
            ):
                self.state.world = newState.world
                self._info += "Upravuji stav světa"
        if newState.map != originalState.map:
            if self._ensure(
                originalState.map == currentState.map,
                "Stavy políček se liší, nemůžu aplikovat změny",
            ):
                self.state.map = newState.map
                self._info += "Upravuji stav mapy"
        teams = set(currentState.teamStates.keys())
        self._ensureStrong(
            set(originalState.teamStates.keys()) == teams,
            "Seznam týmů se změnil, nemůžu aplikovat změny.",
        )
        self._ensureStrong(
            set(originalState.teamStates.keys()) == teams,
            "Nelze měnit seznam týmů.",
        )
        for t in teams:
            if newState.teamStates[t] != originalState.teamStates[t]:
                if self._ensure(
                    originalState.teamStates[t] == currentState.teamStates[t],
                    f"Stavy týmu {t} se liší, nemůžu aplikovat změny.",
                ):
                    self.state.teamStates[t] = newState.teamStates[t]
                    self._info += f"Upravuji stav týmu {t.name}"

        self._ensureValid()
        try:
            x = stateSerialize(self.state)
            stateDeserialize(GameState, x, self.entities)
        except Exception as e:
            tb = traceback.format_exc()
            raise ActionFailed(
                MessageBuilder(
                    "Upravený stav není možné serializovat:", f"```\n{tb}\n```"
                )
            )

        self._info += "Úspěsně provedeno"
