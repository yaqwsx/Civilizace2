from game.forms.action import MoveForm
from game.models.actionMovesList import ActionMove
from game.models.actionBase import Action

class NextGenerationForm(MoveForm):
    pass

class NextGenerationAction(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionMove.nextGeneration
        form = NextGenerationForm

    def build(data):
        action = NextGenerationAction(team=data["team"], move=data["action"], arguments={})
        return action

    def initiate(self, state):
        return True, ""

    def commit(self, state):
        print("State: " + str(state))
        world = state.worldState
        print("world: " + str(world))
        world.generation.nextGeneration()
        message = """Začala generace {gen}""".format(gen=world.generation.generation)
        return True, message
