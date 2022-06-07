from typing import Optional
from game.actions.actionBase import ActionArgs, ActionBase
from game.entities import MapTileEntity, Team
from game.state import ArmyGoal, ArmyId


class ActionArmyDeployArgs(ActionArgs):
    team: Team
    army: ArmyId
    tile: MapTileEntity
    goal: ArmyGoal
    equipment: int
    friendlyTeam: Optional[Team] # Support mode allows chosing a team to support; should be defaulted to the team currently occupying target tile

class ArmyDeploy(ActionBase):
    pass
