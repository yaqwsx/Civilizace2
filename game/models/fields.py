# See https://medium.com/@philamersune/using-postgresql-jsonfield-in-sqlite-95ad4ad2e5f1

import json

from django.conf import settings
from django.contrib.postgres.fields import (
    JSONField as DjangoJSONField,
    ArrayField as DjangoArrayField,
)
from django.db.models import Field, Model
from django.core import serializers


class JSONField(DjangoJSONField):
    pass

class ArrayField(DjangoArrayField):
    pass

if 'sqlite' in settings.DATABASES['default']['ENGINE']:
    class JSONField(Field):
        def db_type(self, connection):
            return 'text'

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


    class ArrayField(JSONField):
        def __init__(self, base_field, size=None, **kwargs):
            """Care for DjanroArrayField's kwargs."""
            self.base_field = base_field
            self.size = size
            return super().__init__(**kwargs)

        def deconstruct(self):
            """Need to create migrations properly."""
            name, path, args, kwargs = super().deconstruct()
            kwargs.update({
                'base_field': self.base_field.clone(),
                'size': self.size,
            })
            return name, path, args, kwargs

class DbList(list):
    def __init__(self, model_type):
        self.model_type = model_type

    def get(self, **kwargs):
        print(type(self))
        def eq(field, value):
            if isinstance(field, Model):
                return field.pk == value
            return field == value
        for item in self:
            if all([eq(getattr(item, arg), value) for arg, value in kwargs.items()]):
                return item
        raise self.model_type.DoesNotExist()

class ListField(Field):
    def __init__(self, model_type, **kwargs):
        self.model_type = model_type
        return super().__init__(**kwargs)

    def deconstruct(self):
        """Need to create migrations properly."""
        name, path, args, kwargs = super().deconstruct()
        kwargs.update({
            'model_type': self.model_type
        })
        return name, path, args, kwargs

    def db_type(self, connection):
            return 'text'

    def from_db_value(self, value, expression, connection):
        if value is not None:
            return self.to_python(value)
        return DbList(self.model_type)

    def to_python(self, value):
        items = DbList(self.model_type)
        if value is not None:
            for obj in serializers.deserialize("json", value):
                items.append(self.model_type.objects.get(pk=obj.object.pk))
        return items

    def get_prep_value(self, value):
        if value is not None:
            for model in value:
                model.save()
            return serializers.serialize("json", value)
        return None

