from django import template

register = template.Library()

@register.filter(name="noNewline")
def noNewline(value):
    return value.replace("\n", "")

def distKey(d, k):
    return d[k]

# Taken from https://stackoverflow.com/questions/29716023/add-class-to-form-field-django-modelform
@register.filter(name="addClasses")
def addClasses(value, arg):
    '''
    Add provided classes to form field
    :param value: form field
    :param arg: string of classes seperated by ' '
    :return: edited field
    '''
    css_classes = value.field.widget.attrs.get('class', '')
    # check if class is set or empty and split its content to list (or init list)
    if css_classes:
        css_classes = css_classes.split(' ')
    else:
        css_classes = []
    # prepare new classes to list
    args = arg.split(' ')
    for a in args:
        if a not in css_classes:
            css_classes.append(a)
    # join back to single string
    return value.as_widget(attrs={'class': ' '.join(css_classes)})

