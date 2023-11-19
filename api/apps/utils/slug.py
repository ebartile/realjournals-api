from django.template.defaultfilters import slugify as django_slugify

import time

from unidecode import unidecode


def slugify(value):
    """
    Return a slug
    """
    return django_slugify(unidecode(value or ""))


def slugify_uniquely(value, model, slugfield="slug"):
    """
    Returns a slug on a name which is unique within a model's table
    """

    suffix = 0
    potential = base = django_slugify(unidecode(value))
    if len(potential) == 0:
        potential = 'null'
    while True:
        if suffix:
            potential = "-".join([base, str(suffix)])
        if not model.objects.filter(**{slugfield: potential}).exists():
            return potential
        suffix += 1


def slugify_uniquely_for_queryset(value, queryset, slugfield="slug"):
    """
    Returns a slug on a name which doesn't exist in a queryset
    """

    suffix = 0
    potential = base = django_slugify(unidecode(value))
    if len(potential) == 0:
        potential = 'null'
    while True:
        if suffix:
            potential = "-".join([base, str(suffix)])
        if not queryset.filter(**{slugfield: potential}).exists():
            return potential
        suffix += 1

