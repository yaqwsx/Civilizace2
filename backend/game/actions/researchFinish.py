from typing import Dict
from game.actions.actionBase import ActionBase, ActionFailed
from game.actions.researchStart import ActionResearchArgs
from game.entities import Resource, Tech, dieName

class ActionResearchFinish(ActionResearchArgs):
    pass


class ActionResearchFinish(ActionBase):
    @property
    def args(self) -> ActionResearchArgs:
        assert isinstance(self._generalArgs, ActionResearchArgs)
        return self._generalArgs

    @property
    def description(self):
        return f"Dokončení výzkumu {self.args.tech.name} ({self.args.team.name})"

    def cost(self) -> Dict[Resource, int]:
        return {}

    def _commitImpl(self) -> None:
        if self.args.tech in self.teamState.techs:
            raise ActionFailed(f"Technologie [[{self.args.tech.id}]] je již vyzkoumána.")

        if not self.args.tech in self.teamState.researching:
            raise ActionFailed(f"Výzkum technologie [[{self.args.tech.id}]] aktuálně neprobíhá, takže ji nelze dokončit.")

        self.teamState.researching.remove(self.args.tech)
        self.teamState.techs.add(self.args.tech)
        self._info += "Výzkum technologie [[" + self.args.tech.id + "]] byl dokončen."
        self._info += f"Vydejte týmu jeden žeton objevu {[dieName(die) for die in self.teamState.getUnlockingDice(self.args.tech)]}"

        # check bonuses
        if self.args.tech.bonuses != "":
            for bonus in [x.strip() for x in self.args.tech.bonuses.split(",")]:
                if bonus == "cheapDie":
                    discount = len([tech for tech in self.teamState.techs if "cheapDie" in tech.bonuses])
                    self.teamState.throwCost = 10 - discount
                    continue
                