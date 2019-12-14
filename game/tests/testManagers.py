from django.test import TestCase
from django.db import models
from game.models import Team, State

class StateManagerTest(TestCase):
    def setUp(self):
        for i in range(2):
            Team.objects.create(name="Team {}".format(i + 1))
        s = State.objects.createInitial()
        self.initialPk = s.pk

    def test_latest(self):
        self.assertEqual(State.objects.getNewest().pk, self.initialPk)
        s1 = State.objects.createInitial()
        self.assertNotEqual(State.objects.getNewest().pk, self.initialPk)
        self.assertEqual(State.objects.getNewest().pk, s1.pk)
        s2 = State.objects.createInitial()
        self.assertNotEqual(State.objects.getNewest().pk, self.initialPk)
        self.assertNotEqual(State.objects.getNewest().pk, s1.pk)
        self.assertEqual(State.objects.getNewest().pk, s2.pk)

