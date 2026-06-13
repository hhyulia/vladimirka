from django import template

register = template.Library()


@register.filter
def image_focus_style(obj):
    if obj is None:
        return 'object-position: 50% 20%;'
    x = getattr(obj, 'image_focus_x', 50)
    y = getattr(obj, 'image_focus_y', 20)
    return f'object-position: {x}% {y}%;'
