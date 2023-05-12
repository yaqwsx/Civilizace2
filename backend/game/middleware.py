
import itertools
import json
from math import floor
import os
import sys
from typing import Iterable
from game.actions.nextTurn import NextTurnAction, NextTurnArgs
from game.gameGlue import stateSerialize
from game.models import DbAction, DbEntities, DbInteraction, DbScheduledAction, DbState, DbTick, DbTurn, GameTime, InteractionType
from django.utils import timezone
from django.db import transaction

from game.viewsets.action_view_helper import ActionViewHelper


@transaction.atomic
def updateTurn():
    """
    Advances turn if needed.
    """
    # First, check if there is an active turn:
    try:
        activeTurn = DbTurn.getActiveTurn()
        assert activeTurn.startedAt is not None
        remaining = activeTurn.startedAt + \
            timezone.timedelta(seconds=activeTurn.duration) - timezone.now()
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

    action = ActionViewHelper.constructActionFromType(
        NextTurnAction, {}, entities, state)
    dbAction = DbAction.objects.create(
        actionType=NextTurnAction.__name__,
        entitiesRevision=entityRevision,
        args=stateSerialize(action.args))

    action.commit()
    ActionViewHelper.dbStoreInteraction(dbAction, dbState,
                                     InteractionType.commit, user=None, state=state, action=action)

    ActionViewHelper._markMapDiff(prevState, state)


def updateScheduledActions():
    try:
        turn = DbTurn.getActiveTurn()
        assert turn.startedAt is not None
        secondsIn = floor((timezone.now() - turn.startedAt).total_seconds())
        current = GameTime(round=turn, time=secondsIn)
    except DbTurn.DoesNotExist:
        return

    pending = sorted(((targetTime, action)
                      for action in DbScheduledAction.objects.filter(performed=False)
                      if (targetTime := action.targetGameTime()) is not None
                      if targetTime <= current),
                     key=lambda x: x[0])
    for _, scheduled in pending:
        try:
            ActionViewHelper.performScheduledAction(scheduled)
        except Exception as e:
            sys.stderr.write("*** SCHEDULED ACTION FAILED***\n")
            sys.stderr.write(f"Action ID: {scheduled.action.id}\n")
            sys.stderr.write(f"Source Action ID: {scheduled.created_from.id}\n")
            sys.stderr.write(f"Action Type: {scheduled.action.actionType}\n")
            sys.stderr.write(json.dumps(scheduled.action.args, indent=4))
            sys.stderr.write(f"Exception: {e}")
            import traceback
            tb = traceback.format_exc()
            sys.stderr.write(tb)


def turnUpdateMiddleware(get_response):
    def middleware(request):
        updateTurn()
        return get_response(request)
    return middleware


def scheduledActionsMiddleware(get_response):
    def middleware(request):
        updateScheduledActions()
        return get_response(request)
    return middleware
