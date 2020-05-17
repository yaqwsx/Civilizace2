from game import forms
from game.models import Action, ActionMove

class NextGenerationAction(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionMove.nextGeneration
        form = forms.NextTurnForm

    def build(data):
        action = NextGenerationAction(team=data["team"], move=data["action"], arguments={})
        return action

    def commit(self, state):
        print("State: " + str(state))
        world = state.worldState
        print("world: " + str(world))
        world.generation.nextGeneration()
        message = """Začala generace {gen}""".format(gen=world.generation.generation)
        return True, message
