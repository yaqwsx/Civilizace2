from django import forms
import datetime
from theme.widgets import FlatpickerDateTime

class MessageForm(forms.Form):
    appearDateTime = forms.DateTimeField(label="Zobrazit zprávu od",
        input_formats=["%H:%M %d. %m. %Y", "%H:%M %d.%m.%Y"],
        initial=datetime.datetime.now(),
        widget=FlatpickerDateTime()
    )
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
                    "appearDateTime": message.appearDateTime,
                    "content": message.content
                }, *args, **kwargs)

class TeamVisibilityForm(forms.Form):
    team = forms.IntegerField(widget=forms.HiddenInput())
    visible = forms.BooleanField(required=False)