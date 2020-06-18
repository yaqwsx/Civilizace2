from .nextTurn import NextTurn
from .worldActions import NextGenerationAction
from .createInitial import CreateInitialMove
from .nextTurn import NextTurn
from .sandboxIncreaseCounter import SandboxIncreaseCounterMove
from .startRound import StartRoundMove
from .research import ResearchMove
from .finishResearch import FinishResearchMove
from .vyroba import VyrobaMove
from .sandbox import SandboxMove
from .godmode import GodmodeForm
from .foodSupply import FoodSupplyMove
from .setBuildingDistance import SetBuildingDistanceMove
from .setTeamDistance import SetTeamDistanceMove
from .withdraw import WithdrawMove

def buildActionMove(data):
    """
    Take an associated form data and build the actionMove
    """
    from game.models.actionBase import Action
    move = data["action"]
    for actionClass in  Action.__subclasses__():
        if actionClass.CiviMeta.move == move:
            return actionClass.build(data=data)
    return None

def formForActionMove(move):
    from game.models.actionBase import Action
    for actionClass in Action.__subclasses__():
        if actionClass.CiviMeta.move == move:
            return actionClass.CiviMeta.form
    return None

def allowedActionMoves(org):
    from game.models.actionBase import Action
    orgGroups = list([x.name for x in org.groups.all()])
    return [c.CiviMeta.move for c in Action.__subclasses__()
            if not set(c.CiviMeta.allowed).isdisjoint(orgGroups)]