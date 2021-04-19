import json
import copy

from django.db import models
from django_enumfield import enum

from .immutable import ImmutableModel
from .fields import JSONField
from game.models.actionTypeList import ActionType

class ActionPhase(enum.Enum):
    initiate = 0
    commit = 1
    abandon = 2
    cancel = 3

class ActionEventManager(models.Manager):
    def createInitial(self):
        return self.create(
            author = None,
            phase=ActionPhase.commit,
            action=Action.objects.createInitial(),
            workConsumed=0)

class ActionEvent(ImmutableModel):
    created = models.DateTimeField("Time of creating the action", auto_now=True)
    author = models.ForeignKey("User", on_delete=models.PROTECT, null=True)
    phase = enum.EnumField(ActionPhase)
    action = models.ForeignKey("Action", on_delete=models.PROTECT)
    workConsumed = models.IntegerField()

    objects = ActionEventManager()

    def applyTo(self, state):
        """
        Apply current step to the state.

        Return value: tuple< bool, str >. First value indicate success, second
        value is a message for the org - either extra instructions or failure
        reason. The message can use HTML tags to further format it.
        """
        if self.phase == ActionPhase.initiate:
            res, message = self.action.initiate(state)
            if res:
                self.initiate(state)
            return res, message
        if self.phase == ActionPhase.commit:
            res, message = self.action.commit(state)
            if res:
                self.commit(state)
            return res, message
        if self.phase == ActionPhase.abandon:
            res, message = self.action.abandon(state)
            if res:
                self.abandon(state)
            return res, message
        if self.phase == ActionPhase.cancel:
            res, message = self.action.cancel(state)
            if res:
                self.cancel(state)
            return res, message
        raise ValueError("Invalid action phase specified")

    def initiate(self, state):
        pass

    def commit(self, state):
        if not self.action.team:
            return
        assert state.teamState(self.action.team.id).resources.getAmount("res-prace") >= self.workConsumed
        state.teamState(self.action.team.id).resources.spendWork(self.workConsumed)

    def abandon(self, state):
        if not self.action.team:
            return
        assert state.teamState(self.action.team.id).resources.getAmount("res-prace") >= self.workConsumed
        state.teamState(self.action.team.id).resources.spendWork(self.workConsumed)

    def cancel(self, state):
        pass

    @staticmethod
    def initiateAction(author, action):
        return ActionEvent(author=author, phase=ActionPhase.initiate,
            action=action, workConsumed=0)

    @staticmethod
    def cancelAction(author, action):
        return ActionEvent(author=author, phase=ActionPhase.cancel,
                action=action, workConsumed=0)

    @staticmethod
    def commitAction(author, action, workConsumed):
        return ActionEvent(author=author, phase=ActionPhase.commit,
                action=action, workConsumed=workConsumed)

    @staticmethod
    def abandonAction(author, action, workConsumed):
        return ActionEvent(author=author, phase=ActionPhase.abandon,
                action=action, workConsumed=workConsumed)

class ActionManager(models.Manager):
    def createInitial(self):
        return self.create(move=ActionType.createInitial, arguments={})

class InvalidActionException(Exception):
    pass

class Action(ImmutableModel):
    team = models.ForeignKey("Team", on_delete=models.PROTECT, null=True)
    move = enum.EnumField(ActionType)
    arguments = JSONField()

    objects = ActionManager()

    @staticmethod
    def stripData(data):
        data = copy.copy(data)
        del data["team"]
        del data["action"]
        return data

    def teamState(self, state):
        return state.teamState(self.team.id)

    def requiresDice(self, state):
        return False

    def dotsRequired(self, state):
        """
        Return dictionary of <dice type> -> number of dots required. The rules
        are treated as OR rules.
        """
        raise NotImplementedError("This action does not require a dice throw")

    @staticmethod
    def relevantEntities(state, team):
        """
        Return list of all relevant game entities for given team. This method is
        a static one as no action of this type exist in the time of invocation.
        """
        raise NotImplementedError("Action base class - did you forget to implement relevantEntities?")

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
        raise NotImplementedError("Action base class - did you forget to implement initiate?")

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
        raise NotImplementedError("Action base class - did you forget to implement abandon?")

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
        raise NotImplementedError("Action base class - did you forget to implement cancel?")

    def resolve(self):
        for actionClass in  Action.__subclasses__():
            if actionClass.CiviMeta.move == self.move:
                return actionClass.objects.get(pk=self.pk)
        return None

    def sane(self):
        """
        Check if the action is sane and can be safely applied
        """
        return self.move is not None and self.team is not None

    def __str__(self):
        return json.dumps(self._dict)

    def diceThrowMessage(self, state):
        required = self.dotsRequired(state)
        message = ""
        if len(required) - 1:
            message += "Pro splnění akce je třeba hodit jedno z následujícího:<ul>"

        for dice, dots in self.dotsRequired(state).items():
            message += "<li><b>{}</b>: {} bodů</li>".format(dice.label, dots)
        message += "</ul>"
        return message

    def description(self):
        return "{} pro tým {}".format(self.move.label, self.team.name)

    def cancelMessage(self):
        return "Akce \"{}\" byla zrušena.".format(self.description())

    def abandonMessage(self):
        return "Akce \"{}\" byla uzavřena neúspěchem. Týmu se nepovedlo hodit dostatek".format(self.description())
