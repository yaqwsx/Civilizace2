from django.db import models
from .immutable import ImmutableModel
from .fields import JSONField
from game.managers import ActionManager, ActionStepManager
import json
from django_enumfield import enum
from django.contrib.auth.models import User

class Dice(enum.Enum):
    tech = 0
    political = 1

    __labels__ = {
        tech: "Technologická kostka",
        political: "Politická kostka"
    }

class ActionPhase(enum.Enum):
    initiate = 0
    commit = 1
    abandon = 2
    cancel = 3

# There are several scenarios for creating an action:
# - the action is created and immediately committed.
# - the action is initiated and then it has to be either committed, abandoned or
#   canceled
class ActionStep(ImmutableModel):
    created = models.DateTimeField("Time of creating the action", auto_now=True)
    author = models.ForeignKey("User", on_delete=models.PROTECT, null=True)
    phase = enum.EnumField(ActionPhase)
    action = models.ForeignKey("Action", on_delete=models.PROTECT)
    workConsumed = models.IntegerField()

    objects = ActionStepManager()

    def applyTo(self, state):
        """
        Apply current step to the state.

        Return value: tuple< bool, str >. First value indicate success, second
        value is a message for the org - either extra instructions or failure
        reason. The message can use HTML tags to further format it.
        """
        if self.phase == ActionPhase.initiate:
            return self.action.initiate(state)
        if self.phase == ActionPhase.commit:
            return self.action.commit(state)
        if self.phase == ActionPhase.abandon:
            return self.action.abandon(state)
        if self.phase == ActionPhase.cancel:
            return self.action.cancel(state)
        raise ValueError("Invalid action phase specified")

    @staticmethod
    def initiateAction(author, action):
        """
        Return appropriate ActionStep for given action (either commit or
        initiate) for the action. The user is the organizer filling the form
        """
        if action.requiresDice():
            return ActionStep(author=author, phase=ActionPhase.initiate,
                action=action, workConsumed=0)
        return ActionStep(author=author, phase=ActionPhase.commit,
                action=action, workConsumed=0)

class ActionMove(enum.Enum):
    createInitial = 0
    sanboxIncreaseCounter = 1
    startNewRound = 2

    __labels__ = {
        createInitial: "Vytvořit nový stav",
        sanboxIncreaseCounter: "Zvýšit counter",
        startNewRound: "Začít kolo"
    }

class Action(ImmutableModel):
    team = models.ForeignKey("Team", on_delete=models.PROTECT, null=True)
    move = enum.EnumField(ActionMove)
    arguments = JSONField()

    objects = ActionManager()

    def teamState(self, state):
        return state.teamState(self.team.id)

    def requiresDice(self):
        return False

    def dotsRequired(self):
        """
        Return dictionary of <dice type> -> number of dots required. The rules
        are treated as OR rules.
        """
        raise NotImplementedError("This action does not require a dice throw")

    def initiate(self, state):
        """
        Apply "initiate" step of this action to the state. Initiation can
        allocate some of the resources - which can be returned in the abondon
        step.

        Return value: tuple< bool, str >. First value indicate success, second
        value is a message for the org - either extra instructions or failure
        reason. The message can use HTML tags to further format it.

        When false is returned the state is undefined state and it should not be
        used by the caller anymore.
        """
        raise NotImplementedError("This action does not require a dice throw - no initiate step is avialable")

    def commit(self, state):
        """
        Apply "commit" step of this action to the state.
        Commiting actions means apply all effects to the state

        Return value: tuple< bool, str >. First value indicate success, second
        value is a message for the org - either extra instructions or failure
        reason. The message can use HTML tags to further format it.

        When false is returned the state is undefined state and it should not be
        used by the caller anymore.
        """
        raise NotImplementedError("Action base class - did you forget to implement commit?")

    def abandon(self, state):
        """
        Apply "abandon" step of this action to the state.
        Abandoning action means further requirements (dice throw) was unsuccessful

        Return value: tuple< bool, str >. First value indicate success, second
        value is a message for the org - either extra instructions or failure
        reason. The message can use HTML tags to further format it.

        When false is returned the state is undefined state and it should not be
        used by the caller anymore.
        """
        raise NotImplementedError("This action does not require a dice throw - no abandon step is avialable")

    def cancel(self, state):
        """
        Cancel initiated action - basically rollback all effects by the initiate
        step. Only actions with initiate step can be cancelled.

        Return value: tuple< bool, str >. First value indicate success, second
        value is a message for the org - either extra instructions or failure
        reason. The message can use HTML tags to further format it.

        When false is returned the state is undefined state and it should not be
        used by the caller anymore.
        """
        raise NotImplementedError("This action does not require a dice throw - no initiate step is avialable")

    def resolve(self):
        import game.models.action # Required to load all subclasses
        for actionClass in  Action.__subclasses__():
            if actionClass.CiviMeta.move == self.move:
                return actionClass.objects.get(pk=self.pk)
        return None

    def sane(self):
        """
        Check if the action is sane and can be safely applied
        """
        return move is not None and team is not None

    def build(data):
        """
        Take an associated form data and build the action
        """
        import game.models.action # Required to load all subclasses
        move = data["action"]
        for actionClass in  Action.__subclasses__():
            if actionClass.CiviMeta.move == move:
                return actionClass.build(data=data)
        return None

    def formFor(move):
        import game.models.action # Required to load all subclasses
        for actionClass in  Action.__subclasses__():
            if actionClass.CiviMeta.move == move:
                return actionClass.CiviMeta.form
        return None

    def __str__(self):
        return json.dumps(self._dict)