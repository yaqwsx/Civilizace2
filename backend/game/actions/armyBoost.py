from game.actions.actionBase import TeamActionBase, TeamActionArgs
from game.actions.armyDeploy import ArmyGoal
from game.actions.common import ActionException, ActionCost, DebugException
from game.entities import Tech, Team
from game.state import ArmyId, ArmyState

class ActionBoostArgs(TeamActionArgs):
    team: Team
    prestige: int
    boost: int

    @property
    def armyId(self):
        return ArmyId(team=self.team, prestige=self.prestige)

class ActionBoost(TeamActionBase):
    args: ActionBoostArgs


    def commitInternal(self) -> None:
        army = self.teamState.armies.get(self.args.armyId)
        if army == None:
            raise DebugException("Neznáná armáda {}".format(self.args.armyId))
        if army.boost >= 0:
            raise ActionException("Armáda už byla před soubojem podpořena.")
        if self.args.boost < 0:
            raise DebugException("Nelze podpořit armádu zápornou hodnotou.")
        if army.state != ArmyState.Marching:
            raise ActionException("Armáda <<{}>> aktuálně neútočí na žádné pole.".format(self.args.armyId))
        if army.goal == ArmyGoal.Supply:
            raise ActionException("Armáda <<{}>> nelze podpořit, protože nebude na poli <<{}>> bojovat.".format(army.id, army.tile))
        army.boost = self.args.boost
        self.info.add("Armáda <<{}>> podpořena {} body pro souboj na poli <<{}>>".format(army.id, army.boost, army.tile))
