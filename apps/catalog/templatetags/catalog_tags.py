from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def query_transform(context, **kwargs):
    """
    Transforms the current GET query dictionary by adding, updating, or removing parameters.
    Keeps combinable filters intact across pagination links (Requirement B1).
    """
    query = context['request'].GET.copy()
    for k, v in kwargs.items():
        if v is not None and v != '':
            query[k] = v
        else:
            query.pop(k, None)
    return query.urlencode()
