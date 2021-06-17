from .nextTurn import NextTurn
from .worldActions import NextGenerationAction
from .createInitial import CreateInitialMove
from .nextTurn import NextTurn
from .sandboxIncreaseCounter import SandboxIncreaseCounterMove
from .startRound import StartRoundMove
from .research import ResearchMove
from .finishResearch import FinishResearchMove
from .vyroba import VyrobaMove
from .enhancer import EnhancerMove
from .sandbox import SandboxMove
from .godmode import GodmodeForm
from .foodSupply import FoodSupplyMove
from .withdraw import WithdrawMove
from .trade import TradeMove
from .spendWork import SpendWorkMove
from .addSticker import AddStickerMove
from .startTask import StartTaskMove
from .finishTask import FinishTaskMove

from .islandDiscover import IslandDiscoverMove
from .islandExplore import IslandExploreMove
from .islandColonize import IslandColonizeMove
from .islandAttack import IslandAttackMove
from .islandResearch import IslandResearchMove
from .islandShare import IslandShareMove
from .islandTransfer import IslandTransferMove
from .islandRepair import IslandRepairMove

from .initialStickers import InitialStickersMove


def buildAction(data):
    """
    Take an associated form data and build the action
    """
    from game.models.actionBase import Action
    move = data["action"]
    for actionClass in  Action.__subclasses__():
        if actionClass.CiviMeta.move == move:
            return actionClass.build(data=data)
    return None

def formForActionType(move):
    from game.models.actionBase import Action
    for actionClass in Action.__subclasses__():
        if actionClass.CiviMeta.move == move:
            return actionClass.CiviMeta.form
    return None

def allowedActionTypes(org):
    from game.models.actionBase import Action
    orgGroups = list([x.name for x in org.groups.all()])
    return [c.CiviMeta.move for c in Action.__subclasses__()
            if not set(c.CiviMeta.allowed).isdisjoint(orgGroups)]