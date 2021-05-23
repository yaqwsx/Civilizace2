import json
import copy

from django.db import models
from django.db.models.deletion import PROTECT
from django_enumfield import enum

from .immutable import ImmutableModel
from .fields import JSONField
from game.models.actionTypeList import ActionType
from game.data.entity import (
    EntitiesVersion, EntityModel, DieModel, AchievementModel, TaskModel,
    IslandModel)
from game.data.resource import ResourceModel, ResourceTypeModel
from game.data.tech import TechModel, TechEdgeModel
from game.data.vyroba import VyrobaModel, EnhancementModel
from game.models.stickers import Sticker
from ground.models import GitRevision

class ActionPhase(enum.Enum):
    initiate = 0
    commit = 1
    abandon = 2
    cancel = 3

class ActionEventManager(models.Manager):
    def createInitial(self, context):
        return self.create(
            author = None,
            phase=ActionPhase.commit,
            action=Action.objects.createInitial(context),
            workConsumed=0)

class ActionEvent(ImmutableModel):
    created = models.DateTimeField("Time of creating the action", auto_now=True)
    author = models.ForeignKey("User", on_delete=models.PROTECT, null=True)
    codeRevision = models.ForeignKey(GitRevision, on_delete=PROTECT, null=True)
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
        state.setContext(self.action.context)
        state.action = self
        if self.phase == ActionPhase.initiate:
            res = self.action.initiate(state)
            if res.success:
                self.initiate(state)
            return res
        if self.phase == ActionPhase.commit:
            res = self.action.commit(state)
            if res.success:
                self.commit(state)
            return res
        if self.phase == ActionPhase.abandon:
            res = self.action.abandon(state)
            if res.success:
                self.abandon(state)
            return res
        if self.phase == ActionPhase.cancel:
            res = self.action.cancel(state)
            if res.success:
                self.cancel(state)
            return res
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
            action=action, workConsumed=0,
            codeRevision=GitRevision.objects.getCurrent())

    @staticmethod
    def cancelAction(author, action):
        return ActionEvent(author=author, phase=ActionPhase.cancel,
                action=action, workConsumed=0,
                codeRevision=GitRevision.objects.getCurrent())

    @staticmethod
    def commitAction(author, action, workConsumed):
        return ActionEvent(author=author, phase=ActionPhase.commit,
                action=action, workConsumed=workConsumed,
                codeRevision=GitRevision.objects.getCurrent())

    @staticmethod
    def abandonAction(author, action, workConsumed):
        return ActionEvent(author=author, phase=ActionPhase.abandon,
                action=action, workConsumed=workConsumed,
                codeRevision=GitRevision.objects.getCurrent())

class ActionManager(models.Manager):
    def create(self, *args, entitiesVersion=None, **kwargs):
        if entitiesVersion is None:
            entitiesVersion = EntitiesVersion.objects.latest('id')
        return super().create(*args, **kwargs, entitiesVersion=entitiesVersion)

    def createInitial(self, context):
        return self.create(move=ActionType.createInitial,
            entitiesVersion=context.entitiesVersion, arguments={})

class InvalidActionException(Exception):
    pass

class ActionResult:
    """
    Result of the application of an action to the state
    """
    def __init__(self, success, message, stickers=[]):
        """
        Fist parameter indicates if the application was successful. The message
        will be dislayed to the organizer and it can contain HTML entities for
        formatting. Stickers is a list of Sticker objects representing new
        stickers that the team was awarded.
        """
        self.success = success
        self.message = message
        self.stickers = stickers
        self.startedTasks = []
        self.finishedTasks = []

    def append(self, other):
        """
        Append another result (e.g., when initiating and committing in a single
        step)
        """
        self.success = self.success and other.success
        self.message = self.message + "<br/>" + other.message
        self.stickers.extend(other.stickers)
        self.startedTasks.extend(other.startedTasks)
        self.finishedTasks.extend(other.finishedTasks)

    def addSticker(self, sticker):
        self.stickers.append(sticker)

    def startTask(self, task, viaTech):
        self.startedTasks.append((task, viaTech))

    def finishTask(self, task):
        self.finishedTasks.append(task)

    @staticmethod
    def makeSuccess(message, stickers=None):
        if stickers is None:
            stickers = []
        return ActionResult(True, message, stickers)

    @staticmethod
    def makeFail(message):
        return ActionResult(False, message, [])

class ActionContext:
    """
    Execution context of the action. It is meant to contain game data - e.g.,
    entities in the particular version.
    """
    def __init__(self, entitiesVersion):
        managers = {
            "dies": DieModel,
            "entities": EntityModel,
            "achievements": AchievementModel,
            "islands": IslandModel,
            "resources": ResourceModel,
            "resourceTypes": ResourceTypeModel,
            "techs": TechModel,
            "vyrobas": VyrobaModel,
            "edges": TechEdgeModel
        }
        for name, model in managers.items():
            setattr(self, name, model.manager.fixVersionManger(entitiesVersion))
        self.entitiesVersion = entitiesVersion

    @staticmethod
    def latests():
        return ActionContext(EntitiesVersion.objects.getNewest())


class Action(ImmutableModel):
    team = models.ForeignKey("Team", on_delete=models.PROTECT, null=True)
    move = enum.EnumField(ActionType)
    entitiesVersion = models.ForeignKey("EntitiesVersion", on_delete=models.PROTECT)
    arguments = JSONField()

    objects = ActionManager()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.entitiesVersion_id:
            self.entitiesVersion = EntitiesVersion.objects.getNewest()
        self.context = ActionContext(self.entitiesVersion)

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
        allocate some of the resources - which can be returned in the abandon
        step.

        Return value: ActionResult.

        When false is returned the state is undefined state and it should not be
        used by the caller anymore.
        """
        raise NotImplementedError("Action base class - did you forget to implement initiate?")

    def commit(self, state):
        """
        Apply "commit" step of this action to the state.
        Commiting actions means apply all effects to the state

        Return value: ActionResult

        When false is returned the state is undefined state and it should not be
        used by the caller anymore.
        """
        raise NotImplementedError("Action base class - did you forget to implement commit?")

    def abandon(self, state):
        """
        Apply "abandon" step of this action to the state.
        Abandoning action means further requirements (dice throw) was unsuccessful

        Return value: ActionResult

        When false is returned the state is undefined state and it should not be
        used by the caller anymore.
        """
        raise NotImplementedError("Action base class - did you forget to implement abandon?")

    def cancel(self, state):
        """
        Cancel initiated action - basically rollback all effects by the initiate
        step. Only actions with initiate step can be cancelled.

        Return value: ActionResult

        When false is returned the state is undefined state and it should not be
        used by the caller anymore.
        """
        raise NotImplementedError("Action base class - did you forget to implement cancel?")

    def resolve(self):
        for actionClass in  Action.__subclasses__():
            if actionClass.CiviMeta.move == self.move:
                return actionClass.objects.get(pk=self.pk)
        return None

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

    def makeCancel(self):
        return ActionResult.makeSuccess(f"Akce \"{self.description()}\" byla zrušena.")

    def makeAbandon(self):
        return ActionResult.makeSuccess(f"Akce \"{self.description()}\" byla uzavřena neúspěchem. Týmu se nepovedlo hodit dostatek")
