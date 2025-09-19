from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """Template filter to lookup a key in a dictionary"""
    return dictionary.get(key, [])

@register.filter
def replace(value, args):
    """Usage: {{ value|replace:"old,new" }}"""
    if not value:
        return value
    try:
        old, new = args.split(',')
        return value.replace(old, new)
    except ValueError:
        # fallback kung mali ang format ng args
        return value
