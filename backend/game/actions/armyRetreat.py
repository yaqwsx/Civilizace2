from game.actions.actionBase import TeamActionBase, ActionArgs
from game.actions.armyDeploy import ArmyGoal
from game.actions.common import ActionException, ActionCost, DebugException
from game.entities import Tech, Team
from game.state import ArmyId, ArmyState

class ActionRetreatArgs(ActionArgs):
    team: Team
    prestige: int

    @property
    def armyId(self):
        return ArmyId(team=self.team, prestige=self.prestige)

class ActionRetreat(TeamActionBase):
    args: ActionRetreatArgs

    def commitInternal(self) -> None:
        army = self.teamState.armies.get(self.args.armyId)
        if army == None:
            raise DebugException("Neznáná armáda {}".format(self.args.armyId))
        if army.state == ArmyState.Idle:
            raise ActionException("Armáda [[{}]] není vyslána plnit žádný úkol, takže ji nelze stáhnout.".format(self.args.armyId))
        if army.state == ArmyState.Marching:
            raise ActionException("Armáda [[{}]] se přesouvá na pole [[{}]], takže ji nelze stáhnout.".format(self.args.armyId))
        if army.boost >= 0:
            raise ActionException("Nelze stáhnout armádu [[{}]] těsně před soubojem.".format(army.id))

        tile = self.state.map.tiles.get(army.tile)
        for inboundId in tile.inbound:
            inbound = self.state.getArmy(inboundId)
            if inbound.isBoosted:
                raise ActionException("Nelze stáhnout armádu [[{}]] těsně před soubojem.".format(army.id))

        self.reward[self.entities.zbrane] += army.retreat(self.state)

        return "Armáda [[{}]] se stáhla z pole [[{}]] a je připravena na další rozkazy".format(army.id, army.tile)
