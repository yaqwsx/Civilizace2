# https://stackoverflow.com/questions/1355150/django-when-saving-how-can-you-check-if-a-field-has-changed

from django.db import models
from django.forms.models import model_to_dict
from copy import deepcopy

class TrackedModel(models.Model):
    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super(TrackedModel, self).__init__(*args, **kwargs)
        self.__initial = self._dict

    @property
    def diff(self):
        d1 = self.__initial
        d2 = self._dict
        diffs = [(k, (v, d2[k])) for k, v in d1.items() if v != d2[k]]
        return dict(diffs)

    @property
    def dirty(self):
        return bool(self.diff)

    @property
    def dirtyFields(self):
        return self.diff.keys()

    def save(self, *args, **kwargs):
        super(TrackedModel, self).save(*args, **kwargs)
        self.__initial = self._dict

    @property
    def _dict(self):
        return deepcopy(model_to_dict(self, fields=[field.name for field in
                             self._meta.fields]))

class ImmutableModel(TrackedModel):
    class Meta:
        abstract = True

    @staticmethod
    def saveAndIfDirty(model):
        pk = model.pk
        model.save()
        return pk != model.pk

    def save(self, *args, **kwargs):
        if not self.pk:
            # We have a fresh object, save it directly
            super(ImmutableModel, self).save(*args, **kwargs)
            return

        relationToUpdate = {}
        relativesDirty = False
        for field in self._meta.get_fields():
            if not hasattr(self, field.name):
                continue
            attr = getattr(self, field.name)
            if isinstance(field, models.fields.related.ForeignKey):
                if attr is None:
                    continue
                if not isinstance(attr, TrackedModel):
                    attr.save()
                    continue
                if ImmutableModel.saveAndIfDirty(attr):
                    setattr(self, field.name, attr)
            if isinstance(field, models.fields.related.ManyToManyField):
                if not issubclass(attr.model, TrackedModel):
                    continue
                newRelatives = []
                for relative in attr.all():
                    if ImmutableModel.saveAndIfDirty(relative):
                        relativesDirty = True
                    newRelatives.append(relative)
                relationToUpdate[field] = newRelatives
        if self.dirty or relativesDirty:
            self.pk = None
            super(ImmutableModel, self).save(*args, **kwargs)
            for field, value in relationToUpdate.items():
                attr = getattr(self, field.name)
                attr.set(value, clear=True)


