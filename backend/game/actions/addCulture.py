from decimal import Decimal

from typing_extensions import override

from game.actions.actionBase import NoInitActionBase, TeamActionArgs


class AddCultureArgs(TeamActionArgs):
    culture: int


class AddCultureAction(NoInitActionBase):
    @property
    @override
    def args(self) -> AddCultureArgs:
        args = super().args
        assert isinstance(args, AddCultureArgs)
        return args

    @property
    @override
    def description(self) -> str:
        return f"Přidat {self.args.culture} kultury týmu {self.args.team.name}"

    @override
    def _commitImpl(self) -> None:
        self._ensureStrong(self.args.culture >= 0, "Nemůžu udělit zápornou kulturu")

        tState = self.team_state()
        if self.entities.culture not in tState.resources:
            tState.resources[self.entities.culture] = Decimal(0)
        tState.resources[self.entities.culture] += self.args.culture
        self._info += f"Tým dostal {self.args.culture} kultury. Nyní má {tState.resources[self.entities.culture]}."
