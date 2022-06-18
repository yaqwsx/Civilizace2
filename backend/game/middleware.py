
import json
import os
import sys
from game.actions.common import ActionCost
from game.actions.nextTurn import ActionNextTurn, ActionNextTurnArgs
from game.gameGlue import stateDeserialize, stateSerialize
from game.models import DbAction, DbDelayedEffect, DbEntities, DbInteraction, DbTick, DbTurn, DbState, InteractionType
from django.utils import timezone
from django.db import transaction

from game.viewsets.action import ActionViewSet

@transaction.atomic
def updateTurn():
    """
    Advances turn if needed.
    """
    # First, check if there is an active turn:
    try:
        activeTurn = DbTurn.objects.getActiveTurn()
        remaining = activeTurn.startedAt + timezone.timedelta(seconds=activeTurn.duration) - timezone.now()
        secsRemaining = remaining.total_seconds()
        if secsRemaining > 0:
            return
        nextTurn = activeTurn.next
        if not nextTurn.enabled:
            return
        nextTurn.startedAt = timezone.now()
        nextTurn.save()
        makeNextTurnAction()
        return
    except DbTurn.DoesNotExist:
        pass

    # Check if there is a turn to be activated:
    candidate = DbTurn.objects \
        .filter(enabled=True, startedAt__isnull=True) \
        .order_by("id").first()
    if candidate is None:
        return
    prev = candidate.prev
    if prev is None or prev.startedAt is not None:
        candidate.startedAt = timezone.now()
        candidate.save()
        makeNextTurnAction()

def makeNextTurnAction():
    entityRevision, entities = DbEntities.objects.get_revision()
    dbState = DbState.objects.latest()
    state = dbState.toIr()
    prevState = dbState.toIr()

    action = ActionViewSet.constructAction("ActionNextTurn", {}, entities, state)
    dbAction = DbAction(
            actionType="ActionNextTurn",
            entitiesRevision=entityRevision,
            args=stateSerialize(action.args))
    dbAction.save()

    action.applyInitiate()
    ActionViewSet.dbStoreInteraction(dbAction, dbState,
                    InteractionType.initiate, None, state, action)

    action.applyCommit(0, action.diceRequirements()[1])
    ActionViewSet.dbStoreInteraction(dbAction, dbState,
                    InteractionType.commit, None, state, action)
    ActionViewSet._markMapDiff(prevState, state)

def updateDelayedEffects():
    try:
        turn = DbTurn.objects.getActiveTurn()
        secondsIn = (timezone.now() - turn.startedAt).total_seconds()
    except DbTurn.DoesNotExist:
        return

    pending = DbDelayedEffect.objects \
        .filter(performed=False, round__lte=turn.id, target__lte=secondsIn)
    for effect in pending:
        try:
            ActionViewSet.performDelayedEffect(effect)
        except Exception as e:
            sys.stderr.write("*** ACTION FAILED***\n")
            sys.stderr.write(f"Delayed ID: {effect.id}\n")
            sys.stderr.write(f"Action ID: {effect.action.id}\n")
            sys.stderr.write(f"Action Type: {effect.action.actionType}\n")
            sys.stderr.write(json.dumps(effect.action.args, indent=4))
            import traceback
            tb = traceback.format_exc()
            sys.stderr.write(tb)

@transaction.atomic
def updatePlague():
    delta = 5 if os.environ.get("CIV_SPEED_RUN", None) != "1" else 1
    now = timezone.now()


    tick, _ = DbTick.objects.get_or_create(name="plague", defaults={"lastTick": now})
    if tick.lastTick + timezone.timedelta(minutes=delta) > now:
        return
    entityRevision, entities = DbEntities.objects.get_revision()
    dbState = DbState.objects.latest()
    state = dbState.toIr()

    action = ActionViewSet.constructAction("ActionPlagueTick", {}, entities, state)
    dbAction = DbAction(
            actionType="ActionPlagueTick",
            entitiesRevision=entityRevision,
            args=stateSerialize(action.args))
    dbAction.save()

    action.applyInitiate()
    ActionViewSet.dbStoreInteraction(dbAction, dbState,
                    InteractionType.initiate, None, state, action)

    commitResult = action.applyCommit(0, action.diceRequirements()[1])
    ActionViewSet.addResultNotifications(commitResult)
    ActionViewSet.dbStoreInteraction(dbAction, dbState,
                    InteractionType.commit, None, state, action)

    # tick.lastTick = now
    tick.save()

def turnUpdateMiddleware(get_response):
    def middleware(request):
        updateTurn()
        response = get_response(request)
        return response
    return middleware


def delayedEffectsMiddleware(get_response):
    def middleware(request):
        updateDelayedEffects()
        response = get_response(request)
        return response
    return middleware

def plagueUpdateMiddleware(get_response):
    def middleware(request):
        updatePlague()
        response = get_response(request)
        return response
    return middleware
