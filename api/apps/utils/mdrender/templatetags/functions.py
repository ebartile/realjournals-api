from django_jinja import library
from jinja2 import Markup
from apps.utils.mdrender.service import render


@library.global_function
def mdrender(account, text) -> str:
    if text:
        return Markup(render(account, text))
    return ""
