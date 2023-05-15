import traceback

from typing_extensions import override

from game.actions.actionBase import ActionArgs, NoInitActionBase
from game.actions.common import ActionFailed
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
                self._info.add("Upravuji stav světa")
        if newState.map.armies != originalState.map.armies:
            if self._ensure(
                originalState.world == currentState.world,
                "Stavy armád se liší, nemůžu aplikovat změny",
            ):
                self.state.map.armies = newState.map.armies
                self._info.add("Upravuji stav armád")
        if newState.map.tiles != originalState.map.tiles:
            if self._ensure(
                originalState.world == currentState.world,
                "Stavy políček se liší, nemůžu aplikovat změny",
            ):
                self.state.map.tiles = newState.map.tiles
                self._info.add("Upravuji stav mapy")
        for t in currentState.teamStates.keys():
            if newState.teamStates[t] != originalState.teamStates[t]:
                if self._ensure(
                    originalState.teamStates[t] == currentState.teamStates[t],
                    f"Stavy týmu {t} se liší. Nemůžu aplikovat změny.",
                ):
                    self.state.teamStates[t] = newState.teamStates[t]
                    self._info.add(f"Upravuji stav týmu {t.name}")

        self._ensureValid()
        try:
            x = stateSerialize(self.state)
            stateDeserialize(GameState, x, self.entities)
        except Exception as e:
            tb = traceback.format_exc()
            raise ActionFailed(
                f"Upravený stav není možné serializovat:\n\n```\n{tb}\n```"
            )

        self._info.add("Úspěsně provedeno")
