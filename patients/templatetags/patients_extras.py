from django import template

register = template.Library()

@register.filter
def get_item(dict_obj, key):
    try:
        return dict_obj.get(key, [])
    except Exception:
        return []
