from django import forms
from game.models import Team
from django_enumfield.forms.fields import EnumChoiceField

def captures(what, field):
    field.widget.attrs.update({"data-valueType": what})
    return field

class TeamChoiceField(forms.ModelChoiceField):
    def __init__(self, *args, **kwargs):
        super(TeamChoiceField, self).__init__(
            queryset=Team.objects.all(), *args, **kwargs)

    def label_from_instance(self, obj):
        return "{} ({})".format(obj.name, obj.id)

class EmptyEnumChoiceField(EnumChoiceField):
    def __init__(self, *args, **kwargs):
        super(EmptyEnumChoiceField, self).__init__(*args, **kwargs)
        self.choices = [('', '-----------')] + self.choices