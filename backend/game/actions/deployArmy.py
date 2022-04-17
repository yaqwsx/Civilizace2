from enum import Enum
from typing import Optional
from pydantic import BaseModel
from game.actions.actionBase import TeamActionBase
from game.actions.common import ActionArgumentException, ActionCost, ActionFailedException
from game.entities import Team, MapTileEntity, MapTileEntity
from game.state import Army

class ArmyDeploymentMode(Enum):
    Occupy = 0
    Eliminate = 1
    Support = 2
    Replace = 3

class ActionDeployArmyArgs(BaseModel):
    Team: Team
    army: Army
    tile: MapTileEntity
    mode: ArmyDeploymentMode
    friendlyTeam: Optional[Team] # Support mode allows chosing a team to support; should be defaulted to the team currently occupying target tile

class ActionDeployArmy(TeamActionBase):
    args: ActionDeployArmyArgs

    def cost(self) -> ActionCost:
        return ActionCost()

    def apply(self) -> None:
        None

        self.info += "Armada na vas kasle"
        # TODO: Přidat samolepky
