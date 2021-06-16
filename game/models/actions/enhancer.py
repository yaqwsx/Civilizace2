from django import forms

from game.forms.action import MoveForm
from game.models.actionTypeList import ActionType
from game.models.actionBase import Action, ActionResult
from game.data.entity import DieModel
from game.models.state import ResourceStorage, EnhancerStatusEnum


class EnhancerForm(MoveForm):
    pass

class EnhancerMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionType.enhancer
        form = EnhancerForm
        allowed = ["super"]

    @staticmethod
    def relevantEntities(state, team):
        techs = state.teamState(team.id).techs
        enhancers = set(techs.getEnhancers()) - set(state.teamState(team.id).enhancers.getOwnedEnhancers())

        vyrobas = state.teamState(team.id).techs.availableVyrobas()

        # TODO: Test: if vyroba not available, filter out enhancer
        enhancers = [enhancer for enhancer in enhancers if enhancer.vyroba in vyrobas]

        return list(enhancers)

    @property
    def enhancer(self):
        return self.context.enhancers.get(id=self.arguments["entity"])

    def requiresDice(self, state):
        return True

    def dotsRequired(self, state):
        return {self.enhancer.die: self.enhancer.dots}

    @staticmethod
    def build(data):
        action = EnhancerMove(team=data["team"], move=data["action"], arguments=Action.stripData(data))
        return action

    def initiate(self, state):
        teamState = self.teamState(state)

        try:
            materials = teamState.resources.payResources(self.enhancer.getDeployInputs())
            if materials:
                resMsg = "".join([f'<li>{amount}&times; {res.label}</li>' for res, amount in materials.items()])
                costMessage = f'Tým musí zaplatit: <ul class="list-disc px-4">{resMsg}</ul>'
            else:
                costMessage = "Tým nic neplatí"
        except ResourceStorage.NotEnoughResourcesException as e:
            resMsg = "\n".join([f'{res.label}: {amount}' for res, amount in e.list.items()])
            message = f'Nedostate zdrojů; chybí: <ul class="list-disc px-4">{resMsg}</ul>'
            return ActionResult.makeFail(message)
        return ActionResult.makeSuccess(
            f"""
                Pro zavedení vylepšení <i>{self.enhancer.label}</i> je třeba hodit: {self.enhancer.dots}&times; {self.enhancer.die.label}<br>
                {costMessage}<br>
            """)

    def commit(self, state):
        self.teamState(state).enhancers.set(self.enhancer, 1)
        return ActionResult.makeSuccess(f"""
                Vylepšení <i>{self.enhancer.label}</i> bylo úspěšně zavedeno do provozu<br>
            """)

    def abandon(self, state):
        return self.makeAbandon()

    def cancel(self, state):
        return self.makeCancel()