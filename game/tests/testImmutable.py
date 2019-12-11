from django.test import TestCase
from django.db import models
from game.models.immutable import ImmutableModel
from game.models.managers import DefaultSelectOrPrefetchManager
from game.models import Team, Action, State, WorldState, TeamState, WealthTeamState, PopulationTeamState


class ImmutableTest(TestCase):
    def setUp(self):
        teamStates = []
        for i in range(2):
            team = Team(name="Team {}".format(i + 1))
            team.save()
            wealth = WealthTeamState(data={})
            wealth.save()
            population = PopulationTeamState(data={})
            population.save()
            teamState = TeamState(team=team, wealth=wealth, population=population)
            teamState.save()
            teamStates.append(teamState)

        world = WorldState(data={})
        world.save()
        action = Action(name="A")
        action.save()
        state = State(action=action, worldState=world)
        state.save()
        state.teamStates.all()

        state.teamStates.set(teamStates)
        state.teamStates.all()

    def test_initialValid(self):
        s = State.objects.all()[0]
        # State
        self.assertEqual(s.id, 1)
        # Action
        self.assertEqual(s.action.id, 1)
        self.assertEqual(s.action.name, "A")
        # World state
        self.assertEqual(s.worldState.id, 1)
        self.assertEqual(s.worldState.data, {})
        # Team state A
        sa = s.teamStates.all()[0]
        self.assertEqual(sa.id, 1)
        self.assertEqual(sa.team.name, "Team 1")
        self.assertEqual(sa.wealth.id, 1)
        self.assertEqual(sa.wealth.data, {})
        self.assertEqual(sa.population.id, 1)
        self.assertEqual(sa.population.data, {})
        # Team state B
        sb = s.teamStates.all()[1]
        self.assertEqual(sb.id, 2)
        self.assertEqual(sb.team.name, "Team 2")
        self.assertEqual(sb.wealth.id, 2)
        self.assertEqual(sb.wealth.data, {})
        self.assertEqual(sb.population.id, 2)
        self.assertEqual(sb.population.data, {})

    def test_changeAction(self):
        s = State.objects.all()[0]
        s.action.name = "B"
        s.save()
        # State
        self.assertNotEqual(s.id, 1)
        # Action
        self.assertNotEqual(s.action.id, 1)
        self.assertEqual(s.action.name, "B")
        # The other items should stay intact
        # World state
        self.assertEqual(s.worldState.id, 1)
        self.assertEqual(s.worldState.data, {})
        # Team state A
        sa = s.teamStates.all()[0]
        self.assertEqual(sa.id, 1)
        self.assertEqual(sa.team.name, "Team 1")
        self.assertEqual(sa.wealth.id, 1)
        self.assertEqual(sa.wealth.data, {})
        self.assertEqual(sa.population.id, 1)
        self.assertEqual(sa.population.data, {})
        # Team state B
        sb = s.teamStates.all()[1]
        self.assertEqual(sb.id, 2)
        self.assertEqual(sb.team.name, "Team 2")
        self.assertEqual(sb.wealth.id, 2)
        self.assertEqual(sb.wealth.data, {})
        self.assertEqual(sb.population.id, 2)
        self.assertEqual(sb.population.data, {})

    def test_changeWealth(self):
        s = State.objects.all()[0]
        s.teamStates.all()[0].wealth.data["X"] = 10
        s.save()
        # State
        self.assertNotEqual(s.id, 1)
        # Action
        self.assertEqual(s.action.id, 1)
        self.assertEqual(s.action.name, "A")
        # The other items should stay intact
        # World state
        self.assertEqual(s.worldState.id, 1)
        self.assertEqual(s.worldState.data, {})
        # Team state A
        sa = s.teamStates.get(team__name="Team 1")
        self.assertNotEqual(sa.id, 1)
        self.assertEqual(sa.team.name, "Team 1")
        self.assertNotEqual(sa.wealth.id, 1)
        self.assertEqual(sa.wealth.data, {"X": 10})
        self.assertEqual(sa.population.id, 1)
        self.assertEqual(sa.population.data, {})
        # Team state B
        sb = s.teamStates.get(team__name="Team 2")
        self.assertEqual(sb.id, 2)
        self.assertEqual(sb.team.name, "Team 2")
        self.assertEqual(sb.wealth.id, 2)
        self.assertEqual(sb.wealth.data, {})
        self.assertEqual(sb.population.id, 2)
        self.assertEqual(sb.population.data, {})