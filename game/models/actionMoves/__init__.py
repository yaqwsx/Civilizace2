from .nextTurn import NextTurn
from .worldActions import NextGenerationAction
from .createInitial import CreateInitialMove
from .nextTurn import NextTurn
from .sandboxIncreaseCounter import SandboxIncreaseCounterMove
from .startRound import StartRoundMove
from .research import ResearchMove
from .vyroba import VyrobaMove

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