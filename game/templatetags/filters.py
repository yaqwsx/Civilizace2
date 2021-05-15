from django import template

register = template.Library()

def noNewline(value):
    return value.replace("\n", "")

register.filter("noNewline", noNewline)