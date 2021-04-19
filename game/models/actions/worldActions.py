from game.forms.action import MoveForm
from game.models.actionTypeList import ActionType
from game.models.actionBase import Action

class NextGenerationForm(MoveForm):
    pass

class NextGenerationAction(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionType.nextGeneration
        form = NextGenerationForm
        allowed = ["super"]

    @staticmethod
    def relevantEntities(state, team):
        return []


    def build(data):
        action = NextGenerationAction(team=data["team"], move=data["action"], arguments={})
        return action

    def initiate(self, state):
        return True, ""

    def commit(self, state):
        print("State: " + str(state))
        world = state.worldState
        print("world: " + str(world))
        world.generation += 1
        message = """Začala generace {gen}""".format(gen=world.generation)
        return True, message
