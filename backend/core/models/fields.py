# See https://medium.com/@philamersune/using-postgresql-jsonfield-in-sqlite-95ad4ad2e5f1

import json
import functools

from django.conf import settings
from django.db.models import Field, Model, JSONField as DjangoJSONField
from django.core import serializers


class JSONField(DjangoJSONField):
    pass


if "sqlite" in settings.DATABASES["default"]["ENGINE"]:

    class JSONField(Field):
        def db_type(self, connection):
            return "text"

        def from_db_value(self, value, expression, connection):
            if value is not None:
                return self.to_python(value)
            return value

        def to_python(self, value):
            if value is not None:
                try:
                    return json.loads(value)
                except (TypeError, ValueError):
                    return value
            return value

        def get_prep_value(self, value):
            if value is not None:
                return str(json.dumps(value))
            return value

        def value_to_string(self, obj):
            return self.value_from_object(obj)


class DbList(list):
    def __init__(self, model_type, populate_by=None):
        self.model_type = model_type
        self.populate_by = populate_by
        self._populate()
        # TBA: Quick and dirty
        # proxies = ["__len__", "__getitem__", "__delitem__", "__setitem__",
        #     "__iter__", "__str__", "__repr__", "insert", "append", "extend", "clear"]
        # proxies = [k for k, v in list.__dict__.items() if "method" in str(v)]
        # def f(fnName, self, *args, **kwargs):
        #     self._populate()
        #     getattr(super(DbList, self), fnName)(*args, **kwargs)
        # for p in proxies:
        #     fWrapper = functools.partial(f, p) # To capture p by value
        #     setattr(self, p, types.MethodType(fWrapper, self))

    def _populate(self):
        if self.populate_by is not None:
            super(DbList, self).extend([x() for x in self.populate_by])
            self.populate_by = None

    def get(self, **kwargs):
        def eq(field, value):
            if isinstance(field, Model):
                field = field.pk
            if isinstance(value, Model):
                value = value.pk
            return field == value

        for item in self:
            if all([eq(getattr(item, arg), value) for arg, value in kwargs.items()]):
                return item
        raise self.model_type.DoesNotExist()

    def has(self, **kwargs) -> bool:
        def eq(field, value):
            if isinstance(field, Model):
                field = field.pk
            if isinstance(value, Model):
                value = value.pk
            return field == value

        for item in self:
            if all([eq(getattr(item, arg), value) for arg, value in kwargs.items()]):
                return True
        return False


class ListField(Field):
    def __init__(self, model_type, model_manager=None, **kwargs):
        self.model_type = model_type
        if model_manager is not None:
            self.get_model_manager = model_manager
        else:
            self.get_model_manager = lambda: model_type.objects
        return super().__init__(**kwargs)

    def deconstruct(self):
        """Need to create migrations properly."""
        name, path, args, kwargs = super().deconstruct()
        kwargs.update({"model_type": self.model_type})
        return name, path, args, kwargs

    def db_type(self, connection):
        return "text"

    def from_db_value(self, value, expression, connection):
        if value is not None:
            return self.to_python(value)
        return DbList(self.model_type)

    def to_python(self, value):
        def populate(pk):
            return self.get_model_manager().get(pk=pk)

        if value is not None:
            items = [
                functools.partial(populate, obj.object.pk)
                for obj in serializers.deserialize("json", value)
            ]
        else:
            items = []
        return DbList(self.model_type, items)

    def get_prep_value(self, value):
        if value is not None:
            for model in value:
                model.save()
            return serializers.serialize("json", value)
        return None
