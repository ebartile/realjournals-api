from django_jinja import library
from apps.utils.urls import urls
from django.conf import settings

@library.global_function(name="resolve_landing_url")
def resolve_landing(type, *args):
    url_tmpl = "{scheme}://{domain}{url}"
    url = urls['landing'][type].format(*args)
    return url_tmpl.format(scheme="https", domain=settings.LANDING_HOST, url=url)    

@library.global_function(name="resolve_account_url")
def resolve_account(type, *args):
    url_tmpl = "{scheme}://{domain}{url}"
    url = urls['account'][type].format(*args)
    return url_tmpl.format(scheme="https", domain=settings.ACCOUNT_HOST, url=url)    

@library.global_function(name="resolve_api_url")
def resolve_api(type, *args):
    url_tmpl = "{scheme}://{domain}{url}"
    url = urls['api'][type].format(*args)
    return url_tmpl.format(scheme="https", domain=settings.API_HOST, url=url)    

@library.global_function(name="resolve_terminal_url")
def resolve_terminal(type, *args):
    url_tmpl = "{scheme}://{domain}{url}"
    url = urls['terminal'][type].format(*args)
    return url_tmpl.format(scheme="https", domain=settings.TERMINAL_HOST, url=url)    

@library.global_function(name="resolve_admin_url")
def resolve_admin(type, *args):
    url_tmpl = "{scheme}://{domain}{url}"
    url = urls['admin'][type].format(*args)
    return url_tmpl.format(scheme="https", domain=settings.ADMIN_HOST, url=url)    
