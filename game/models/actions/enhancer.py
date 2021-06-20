from django import forms
from crispy_forms.layout import Layout, HTML

from game.forms.action import MoveForm
from game.models.actionTypeList import ActionType
from game.models.actionBase import Action, ActionResult
from game.data.enhancer import EnhancerModel
from game.models.state import ResourceStorage, EnhancerStatusEnum
from game.models.stickers import Sticker, StickerType

from timeit import default_timer as timer


class EnhancerForm(MoveForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        enhancer = self.getEntity(EnhancerModel)

        layout = [self.commonLayout]

        if enhancer.detail != "":
            layout.append(HTML(f"""<br><b>Zkontroluj podmínku: {enhancer.detail}</b> a až potom dej Odeslat<br><br>"""))
        else:
            layout.append(HTML(f"""<br>Vylepšení nemá žádnou podmínku, můžeš rovnou Odeslat"""))

        self.helper.layout = Layout(
            *layout
        )

class EnhancerMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionType.enhancer
        form = EnhancerForm
        allowed = ["super", "org"]

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
        message = f"""
                Pro zavedení vylepšení <i>{self.enhancer.label}</i> je třeba hodit: {self.enhancer.dots}&times; {self.enhancer.die.label}<br>
                {costMessage}<br>
            """
        if self.enhancer.detail != "":
            message += f"""Podmínka akce: <b>{self.enhancer.detail}</b>"""
        return ActionResult.makeSuccess(message)

    def commit(self, state):
        self.teamState(state).enhancers.set(self.enhancer, 1)
        result = ActionResult.makeSuccess(f"""
                Vylepšení <i>{self.enhancer.label}</i> bylo úspěšně zavedeno do provozu<br>
            """)
        result.addSticker((Sticker(entity=self.enhancer.vyroba, type=StickerType.REGULAR)))
        return result

    def abandon(self, state):
        return self.makeAbandon()

    def cancel(self, state):
        return self.makeCancel()