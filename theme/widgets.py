from django.forms import DateTimeInput

class FlatpickerDateTime(DateTimeInput):
    def __init__(self, *args, **kwargs):
        super(FlatpickerDateTime, self).__init__(
            *args, format="%H:%M %d.%m.%Y", *kwargs
        )
    def get_context(self, name, value, attrs):
        datetimepicker_id = 'datetimepicker_{name}'.format(name=name)
        if attrs is None:
            attrs = dict()
        attrs['class'] = 'datetime'
        context = super().get_context(name, value, attrs)
        context['widget']['datetimepicker_id'] = datetimepicker_id
        return context