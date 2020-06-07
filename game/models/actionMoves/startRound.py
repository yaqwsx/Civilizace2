from game.forms.action import MoveForm
from game.models.actionMovesList import ActionMove
from game.models.actionBase import Action


class StartRoundForm(MoveForm):
    pass

class StartRoundMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionMove.startNewRound
        form = StartRoundForm
        allowed = ["super", "org"]

    @staticmethod
    def relevantEntities(state, team):
        return []


    def build(data):
        action = StartRoundMove(team=data["team"], move=data["action"], arguments={})
        return action

    def initiate(self, state):
        return True, "Začínám začínat nové kolo"

    def commit(self, state):
        populationState = self.teamState(state).population
        populationState.startNewRound()
        message = """
            Začne nové kolo. Tým bude mít:
            <ul>
                <li>{pop} obyvatel</li>
                <li>{work} práce</li>
            <ul>
        """.format(pop=populationState.population, work=populationState.work)
        return True, message