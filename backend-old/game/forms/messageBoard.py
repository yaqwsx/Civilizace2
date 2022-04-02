from django import forms
import datetime
from django.utils import timezone
from theme.widgets import FlatpickerDateTime
from django_enumfield.forms.fields import EnumChoiceField
from game.models.messageBoard import MessageType

class MessageForm(forms.Form):
    appearDateTime = forms.DateTimeField(label="Zobrazit zprávu od",
        input_formats=["%H:%M %d. %m. %Y", "%H:%M %d.%m.%Y"],
        initial=timezone.now(),
        widget=FlatpickerDateTime()
    )
    type = EnumChoiceField(MessageType)
    content = forms.CharField(label="Obsah zprávy",
        widget=forms.Textarea(attrs={
            "oninput": "auto_grow(this)",
            "rows": None
        }))

    def __init__(self, *args, message=None, **kwargs):
        if not message:
            super().__init__(*args, **kwargs)
        else:
            super().__init__(initial={
                    "type": message.type,
                    "appearDateTime": message.appearDateTime,
                    "content": message.content
                }, *args, **kwargs)

class TeamVisibilityForm(forms.Form):
    team = forms.CharField(widget=forms.HiddenInput())
    visible = forms.BooleanField(required=False)