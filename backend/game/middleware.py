
from game.actions.common import ActionCost
from game.actions.nextTurn import ActionNextTurn, ActionNextTurnArgs
from game.gameGlue import stateDeserialize, stateSerialize
from game.models import DbAction, DbDelayedEffect, DbEntities, DbInteraction, DbTurn, DbState, InteractionType
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

    action = ActionNextTurn(entities=entities, state=state, args=ActionNextTurnArgs())
    cost = action.cost()

        # Initiate the action
    initiateResult = action.initiate(cost)
    if not initiateResult.succeeded:
        raise RuntimeError("Nemůžu pokročit v kole. Něco je fakt špatně. Křič na Honzu a Maaru.")
    dbAction = DbAction(
            actionType="ActionNextTurn", entitiesRevision=entityRevision,
            args=stateSerialize(action.args), cost=stateSerialize(cost))
    dbAction.save()
    dbInitiate = DbInteraction(
            phase=InteractionType.initiate,
            action=dbAction,
            author=None)
    dbInitiate.save()
    dbState.updateFromIr(action.state)
    dbState.action = dbInitiate
    dbState.save()

        # Commit the action
    result = action.commit()
    if result.succeeded:
        action.commitReward(result.productions)
    dbCommit = DbInteraction(
            phase=InteractionType.commit,
            action=dbAction,
            author=None)
    dbCommit.save()
    dbState.updateFromIr(action.state)
    dbState.action = dbCommit
    dbState.save()

def updateDelayedEffects():
    try:
        turn = DbTurn.objects.getActiveTurn()
        secondsIn = (timezone.now() - turn.startedAt).total_seconds()
    except DbTurn.DoesNotExist:
        return

    pending = DbDelayedEffect.objects \
        .filter(result__isnull=True, round__lte=turn.id, target__lte=secondsIn)
    for effect in pending:
        ActionViewSet.performDelayedEffect(effect)

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
