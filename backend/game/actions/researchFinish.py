from typing_extensions import override

from game.actions.actionBase import TeamInteractionActionBase
from game.actions.researchStart import ResearchArgs


class ResearchFinishArgs(ResearchArgs):
    pass


class ResearchFinishAction(TeamInteractionActionBase):
    @property
    @override
    def args(self) -> ResearchFinishArgs:
        assert isinstance(self._generalArgs, ResearchFinishArgs)
        return self._generalArgs

    @property
    @override
    def description(self) -> str:
        return f"Dokončení výzkumu {self.args.tech.name} ({self.args.team.name})"

    @override
    def _initiateCheck(self) -> None:
        self._ensureStrong(self.args.tech not in self.teamState.techs,
                           f"Technologie [[{self.args.tech.id}]] je již vyzkoumána.")
        self._ensureStrong(self.args.tech in self.teamState.researching,
                           f"Výzkum technologie [[{self.args.tech.id}]] aktuálně neprobíhá, takže ji nelze dokončit.")

    @override
    def _commitSuccessImpl(self) -> None:
        self.teamState.researching.remove(self.args.tech)
        self.teamState.techs.add(self.args.tech)
        self._info += f"Výzkum technologie [[{self.args.tech.id}]] byl dokončen."
        self._info += f"Vydejte týmu puntík na kostku"
