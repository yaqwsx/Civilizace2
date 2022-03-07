from django.db import models, transaction
from game.models.users import User
from game.models.state import State
from game.models.actionBase import ActionEvent
from game.models.actions.worldActions import NextGenerationAction
from datetime import datetime, timedelta
from django.utils import timezone


class GenerationTickSettings(models.Model):
    period = models.DurationField(default=timedelta(minutes=15), null=True)
    renew = models.BooleanField(default=False)

class ExpectedGeneration(models.Model):
    generationDue = models.DateTimeField(default=None, null=True)
    fulfilled = models.BooleanField(default=False)
    seq = models.IntegerField(default=1)

    @property
    def isDue(self):
        return self.generationDue is not None and timezone.now() > self.generationDue

def getGenerationSettings():
    return GenerationTickSettings.objects.get_or_create(id=1)[0]

def getExpectedGeneration():
    return ExpectedGeneration.objects.filter(fulfilled=False).latest("pk")

@transaction.atomic
def updateGeneration():
    expectedGen = getExpectedGeneration()
    while expectedGen.isDue:
        expectedGen = advanceGeneration(expectedGen)

def advanceGeneration(expectedGen):
    systemUser = user=User.objects.get(username="system")
    state = State.objects.getNewest()
    action = NextGenerationAction.build({
        "team": None,
        "action": NextGenerationAction.CiviMeta.move,
    })
    initiateStep = ActionEvent.initiateAction(None, action)
    initiateStep.applyTo(state)
    commitStep = ActionEvent.commitAction(systemUser, action, 0)
    commitStep.applyTo(state)
    action.save()
    initiateStep.save()
    commitStep.save()
    state.save()
    expectedGen.fulfilled = True
    expectedGen.save()

    settings = getGenerationSettings()
    dueTime = None
    if settings.renew:
        dueTime = expectedGen.generationDue + settings.period
    newExpGen = ExpectedGeneration.objects.create(
        seq=state.worldState.generation,
        generationDue=dueTime)
    return newExpGen


def generationUpdateMiddleware(get_response):
    def middleware(request):
        updateGeneration()
        response = get_response(request)
        return response

    return middleware