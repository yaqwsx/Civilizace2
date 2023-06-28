from typing_extensions import override

from game.actions.actionBase import TeamInteractionActionBase
from game.actions.researchStart import ResearchArgs


class ResearchFinishArgs(ResearchArgs):
    pass


class ResearchFinishAction(TeamInteractionActionBase):
    @property
    @override
    def args(self) -> ResearchFinishArgs:
        args = super().args
        assert isinstance(args, ResearchFinishArgs)
        return args

    @property
    @override
    def description(self) -> str:
        return f"Dokončení výzkumu {self.args.tech.name} ({self.args.team.name})"

    @override
    def _initiateCheck(self) -> None:
        teamState = self.team_state()
        self._ensureStrong(
            self.args.tech not in teamState.techs,
            f"Technologie [[{self.args.tech.id}]] je již vyzkoumána.",
        )
        self._ensureStrong(
            self.args.tech in teamState.researching,
            f"Výzkum technologie [[{self.args.tech.id}]] aktuálně neprobíhá, takže ji nelze dokončit.",
        )

    @override
    def _commitSuccessImpl(self) -> None:
        teamState = self.team_state()
        teamState.researching.remove(self.args.tech)
        teamState.techs.add(self.args.tech)
        self._info += f"Výzkum technologie [[{self.args.tech.id}]] byl dokončen."
        self._info += f"Vydejte týmu puntík na kostku"
