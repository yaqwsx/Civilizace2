from django.test import TestCase
from game.data.update import Update
from game.models.state import ResourceStorageItem, ResourceStorage
from game.data.resource import ResourceModel

class ListFieldTest(TestCase):
    def setUp(self):
        updater = Update()
        updater.fileAsSource("game/data/entities.json")
        updater.update()

        self.initialPk = ResourceStorage.objects.createInitial().pk

    def test_retrieve(self):
        r = ResourceStorage.objects.all()[0]
        self.assertEqual(r.id, self.initialPk)
        self.assertEqual(len(r.items), 2)
        self.assertEqual(r.items[0].resource.id, "res-obyvatel")
        self.assertEqual(r.items[0].amount, 100)
        self.assertEqual(r.items[1].resource.id, "res-prace")
        self.assertEqual(r.items[1].amount, 100)

    def test_modify(self):
        r = ResourceStorage.objects.get(id=self.initialPk)
        r.items[0].amount = 42
        self.assertTrue(r.dirty)
        r.save()
        self.assertTrue(not r.dirty)

        # Check the value was changed
        self.assertEqual(len(r.items), 2)
        self.assertEqual(r.items[0].resource.id, "res-obyvatel")
        self.assertEqual(r.items[0].amount, 42)
        self.assertEqual(r.items[1].resource.id, "res-prace")
        self.assertEqual(r.items[1].amount, 100)

        # Check the original was unchanged
        original = ResourceStorage.objects.get(pk=self.initialPk)
        self.assertEqual(len(original.items), 2)
        self.assertEqual(original.items[0].resource.id, "res-obyvatel")
        self.assertEqual(original.items[0].amount, 100)
        self.assertEqual(original.items[1].resource.id, "res-prace")
        self.assertEqual(original.items[1].amount, 100)

    def test_append(self):
        r = ResourceStorage.objects.get(id=self.initialPk)
        r.items.append(ResourceStorageItem(resource=ResourceModel.objects.get(id="mat-maso"), amount=20))
        self.assertTrue(r.dirty)
        r.save()
        self.assertTrue(not r.dirty)
        self.assertEqual(len(r.items), 3)
        self.assertTrue(r.items[2].id is not None)
        self.assertEqual(r.items[2].resource.label, "Maso")
        self.assertEqual(r.items[2].amount, 20)

    def test_noChange(self):
        r = ResourceStorage.objects.get(id=self.initialPk)
        id = r.items[0].id
        # Modify the other item
        r.items[1].amount = 20
        r.save()
        self.assertEqual(r.items[0].id, id)

    def test_get(self):
        r = ResourceStorage.objects.get(id=self.initialPk)
        found = r.items.get(resource="res-prace")
        self.assertEqual(found.resource.label, "Práce")