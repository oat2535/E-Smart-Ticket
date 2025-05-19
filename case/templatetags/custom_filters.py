# your_app/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def wrap_50(value):
    if not isinstance(value, str):
        return value
    return '<br>'.join([value[i:i+50] for i in range(0, len(value), 50)])
